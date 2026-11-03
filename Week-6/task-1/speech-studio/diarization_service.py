"""Localhost live PCM diarization. SDK callbacks never write to WebSockets."""

import json
from queue import Empty, Full, Queue
from threading import Event, Lock
from time import monotonic
from urllib.parse import urlsplit

import azure.cognitiveservices.speech as sdk
from simple_websocket import ConnectionClosed

import speech_service as shared

MAX_CHUNK_BYTES = 6400  # at most 200 ms of PCM per binary WebSocket message
MAX_SESSION_SECONDS = 60
MAX_SESSION_BYTES = 16000 * 2 * MAX_SESSION_SECONDS
MAX_EVENTS = 128
READY_TIMEOUT = 10
DRAIN_TIMEOUT = 10
STOP_GRACE = 3


def allowed_origin(origin, host):
    try:
        source, server = urlsplit(origin or ""), urlsplit("http://" + host)
        return (source.scheme == "http" and source.hostname in {"localhost", "127.0.0.1", "::1"}
                and source.hostname == server.hostname and (source.port or 80) == (server.port or 80)
                and not source.username and not source.password
                and not source.path and not source.query and not source.fragment)
    except ValueError:
        return False


class LiveSession:
    """One owned transcriber/stream; bounded finals and one coalesced interim."""

    def __init__(self):
        self.transcriber = self.stream = None
        self.connections = []
        self.events = Queue(maxsize=MAX_EVENTS)
        self.state = Lock()
        self.ready_or_error, self.stopped = Event(), Event()
        self.started = False
        self.accepting = True
        self.input_closed = False
        self.error = None
        self.interim = None
        self.final_ids = set()
        self.final_count = 0
        self.total_bytes = 0

    def fail(self, message):
        if self.error is None:
            self.error = message
        self.ready_or_error.set()

    def _guard(self, handler):
        def callback(event):
            with self.state:
                if not self.accepting:
                    return
                try:
                    handler(event)
                except Exception:
                    self.fail("Azure konuşmacı sonucu işlenemedi; oturum tamamlanamadı.")
        return callback

    def _result(self, event, final):
        result = event.result
        if result.reason == sdk.ResultReason.NoMatch:
            return
        expected = sdk.ResultReason.RecognizedSpeech if final else sdk.ResultReason.RecognizingSpeech
        if result.reason != expected:
            self.fail("Azure canlı konuşmayı tamamlayamadı.")
            return
        if not isinstance(result.text, str) or not result.text.strip():
            return
        if len(result.text) > 4000:
            self.fail("Konuşma sonucu tampon sınırını aştı.")
            return
        speaker = result.speaker_id
        speaker = speaker if isinstance(speaker, str) and 0 < len(speaker) <= 128 else "Unknown"
        result_id = result.result_id
        result_id = result_id if isinstance(result_id, str) and len(result_id) <= 128 else ""
        ticks = lambda value: value / 10000 if isinstance(value, int) and value >= 0 else None
        payload = {"type": "final" if final else "interim", "text": result.text,
                   "speaker_id": speaker, "result_id": result_id,
                   "offset_ms": ticks(result.offset), "duration_ms": ticks(result.duration)}
        if not final:
            self.interim = payload
            return
        key = result_id or (payload["offset_ms"], payload["duration_ms"], speaker, result.text)
        if key in self.final_ids:
            return
        if len(self.final_ids) >= MAX_EVENTS:
            self.fail("Kesinleşmiş sonuç sınırına ulaşıldı; oturum tamamlanamadı.")
            return
        self.final_ids.add(key)
        self.interim = None
        try:
            self.events.put_nowait(payload)
            self.final_count += 1
        except Full:
            self.fail("Sonuç kuyruğu doldu; oturum tamamlanamadı.")

    def _canceled(self, event):
        details = event.cancellation_details
        if details.reason == sdk.CancellationReason.EndOfStream:
            return  # Still wait for session_stopped and the final results.
        if details.reason == sdk.CancellationReason.Error:
            messages = {
                sdk.CancellationErrorCode.AuthenticationFailure: "Azure kimlik doğrulaması başarısız. Anahtar ve bölgeyi kontrol edin.",
                sdk.CancellationErrorCode.TooManyRequests: "Azure kota/istek sınırına ulaşıldı. Daha sonra deneyin.",
                sdk.CancellationErrorCode.ConnectionFailure: "Azure bağlantısı kesildi; oturum tamamlanamadı.",
                sdk.CancellationErrorCode.ServiceTimeout: "Azure canlı tanıma zaman aşımına uğradı.",
            }
            self.fail(messages.get(details.code, "Azure canlı konuşma servisi hata verdi."))
        else:
            self.fail("Canlı tanıma iptal edildi; oturum tamamlanamadı.")

    def _started(self, _event):
        self.started = True
        self.ready_or_error.set()

    def open(self, language):
        if language != "en-US":
            raise shared.InvalidAudioError("Canlı diarization yalnızca en-US destekler.")
        settings = shared.load_speech_settings()
        config = sdk.SpeechConfig(subscription=settings.key, region=settings.region)
        config.speech_recognition_language = language
        config.set_property(sdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults, "true")
        audio_format = sdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)
        self.stream = sdk.audio.PushAudioInputStream(stream_format=audio_format)
        audio = sdk.audio.AudioConfig(stream=self.stream)
        self.transcriber = sdk.transcription.ConversationTranscriber(speech_config=config, audio_config=audio)
        for signal, handler in [(self.transcriber.transcribing, lambda event: self._result(event, False)),
                                (self.transcriber.transcribed, lambda event: self._result(event, True)),
                                (self.transcriber.canceled, self._canceled),
                                (self.transcriber.session_started, self._started),
                                (self.transcriber.session_stopped, lambda _event: self.stopped.set())]:
            self.connections.append(signal)
            signal.connect(self._guard(handler))
        shared._wait_sdk_operation(self.transcriber.start_transcribing_async)
        if not self.ready_or_error.wait(READY_TIMEOUT) or not self.started or self.stopped.is_set():
            raise shared.SpeechServiceError(self.error or "Azure canlı oturumu hazır olmadı; tekrar deneyin.")
        if self.error:
            raise shared.SpeechServiceError(self.error)

    def write(self, pcm):
        if self.input_closed or not isinstance(pcm, bytes) or not pcm or len(pcm) % 2 or len(pcm) > MAX_CHUNK_BYTES:
            raise shared.InvalidAudioError("Geçersiz PCM parçası; 16-bit mono 16 kHz ham ses bekleniyor.")
        if self.total_bytes + len(pcm) > MAX_SESSION_BYTES:
            raise shared.InvalidAudioError("Canlı ses en fazla 60 saniye olabilir.")
        self.stream.write(pcm)
        self.total_bytes += len(pcm)

    def end_input(self):
        if self.stream is not None and not self.input_closed:
            self.stream.close()
            self.input_closed = True

    def pending(self):
        items = []
        # Bound each drain so a busy callback producer cannot starve input/deadlines.
        for _ in range(MAX_EVENTS):
            try:
                items.append(self.events.get_nowait())
            except Empty:
                break
        with self.state:
            if self.interim is not None:
                items.append(self.interim)
                self.interim = None
        return items

    def close(self):
        """Owner/request flow only. Keep callbacks alive through the final stop."""
        failures = []
        if self.transcriber is not None:
            try:
                shared._wait_sdk_operation(self.transcriber.stop_transcribing_async)
            except Exception:
                failures.append("stop")
        with self.state:
            self.accepting = False
        for signal in self.connections:
            try:
                signal.disconnect_all()
            except Exception:
                failures.append("disconnect_all")
        try:
            self.end_input()
        except Exception:
            failures.append("stream.close")
        if failures:
            self.fail("Canlı oturumun temizliği tamamlanamadı; sonuç tam başarı sayılmaz.")


def serve_diarization(ws):
    """One WebSocket sender/receiver loop; all SDK traffic is queued by callbacks."""
    session = None
    acquired = False
    error = None
    completed = False

    def send(payload):
        ws.send(json.dumps(payload, ensure_ascii=False))

    def results():
        for item in session.pending():
            send(item)

    try:
        first = ws.receive(timeout=5)
        if not isinstance(first, str) or len(first) > 1024:
            raise shared.InvalidAudioError("Önce start ve en-US dilini gönderin.")
        config = json.loads(first)
        if not isinstance(config, dict) or config.get("type") != "start" or config.get("language") != "en-US":
            raise shared.InvalidAudioError("Canlı diarization yalnızca en-US start isteği kabul eder.")
        acquired = shared._speech_lock.acquire(blocking=False)
        if not acquired:
            raise shared.SpeechBusyError()
        shared._live_session_active.set()
        session = LiveSession()
        session.open("en-US")
        send({"type": "ready", "sample_rate": 16000, "channels": 1, "bits_per_sample": 16,
              "max_seconds": MAX_SESSION_SECONDS, "credits": 4})
        deadline = monotonic() + MAX_SESSION_SECONDS
        stop_requested = drain_deadline = None
        while True:
            results()
            if session.error:
                raise shared.SpeechServiceError(session.error)
            now = monotonic()
            if session.stopped.is_set():
                if not session.input_closed:
                    raise shared.SpeechServiceError("Azure oturumu giriş tamamlanmadan sona erdi.")
                results()
                completed = True
                break
            if drain_deadline is not None and now >= drain_deadline:
                raise shared.SpeechServiceError("Son Azure sonuçları zamanında gelmedi; kısmi sonuçlar tamamlanmış değildir.")
            if not session.input_closed and now >= deadline and stop_requested is None:
                stop_requested = now
                send({"type": "stop_requested", "reason": "duration_limit"})
            if stop_requested is not None and not session.input_closed and now - stop_requested >= STOP_GRACE:
                raise shared.SpeechServiceError("60 saniye sınırında ses akışı zamanında kapatılmadı.")
            data = ws.receive(timeout=0.02)
            if data is None:
                continue
            if isinstance(data, bytes):
                session.write(data)
                send({"type": "ack"})
            elif isinstance(data, str) and len(data) <= 1024:
                command = json.loads(data)
                if not isinstance(command, dict) or command.get("type") != "stop" or session.input_closed:
                    raise shared.InvalidAudioError("Geçersiz canlı oturum komutu.")
                session.end_input()
                drain_deadline = monotonic() + DRAIN_TIMEOUT
                send({"type": "stopping"})
            else:
                raise shared.InvalidAudioError("Geçersiz canlı ses mesajı.")
    except ConnectionClosed:
        error = "WebSocket bağlantısı kesildi; oturum tamamlanmadı."
    except shared.ConfigurationError:
        error = "Azure ayarları eksik. Sunucuda SPEECH_KEY ve SPEECH_REGION ayarlarını tamamlayın."
    except (shared.InvalidAudioError, shared.SpeechServiceError) as caught:
        error = caught.public_message if isinstance(caught, shared.SpeechServiceError) else str(caught)
    except Exception:
        error = "Canlı diarization başlatılamadı veya tamamlanamadı."
    finally:
        try:
            if session is not None:
                session.close()
                error = error or session.error
                # Final callbacks during stop are retained and sent before completed.
                results()
                if completed and not session.final_count:
                    error = error or "Konuşma tanınamadı; tamamlanmış konuşma sonucu yok."
            if error:
                send({"type": "error", "error": error})
            elif completed:
                send({"type": "completed", "final_count": session.final_count})
        except Exception:
            pass  # Disconnected transport cannot receive a completion claim.
        finally:
            if acquired:
                shared._live_session_active.clear()
                shared._speech_lock.release()
            try:
                ws.close()
            except Exception:
                pass
