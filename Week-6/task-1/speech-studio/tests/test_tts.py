"""Offline tests: Azure SDK operations and dotenv file reads are mocked."""

import io
import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as web
import speech_service as service


def sample_wav():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 24)
    return buffer.getvalue()


class TTSTests(unittest.TestCase):
    def setUp(self):
        web.app.config.update(TESTING=True)
        self.client = web.app.test_client()
        self.dotenv = patch.object(service, "load_dotenv").start()
        self.environment = patch.dict(os.environ, {
            "SPEECH_KEY": "unit-test-placeholder",
            "SPEECH_REGION": "eastus",
        }, clear=True).start()
        self.config_factory = patch.object(service.speechsdk, "SpeechConfig").start()
        self.synth_factory = patch.object(service.speechsdk, "SpeechSynthesizer").start()
        self.addCleanup(patch.stopall)
        self.wav = sample_wav()
        self.result = SimpleNamespace(
            reason=service.speechsdk.ResultReason.SynthesizingAudioCompleted,
            audio_data=self.wav,
        )
        self.synth_factory.return_value.speak_text_async.return_value.get.return_value = self.result

    def post(self, **overrides):
        return self.client.post('/api/tts', json={
            'text': 'Hello world', 'language': 'en-US', **overrides,
        })

    def test_success_wav_and_sdk_contract_for_both_languages(self):
        for language, voice in service.VOICES.items():
            with self.subTest(language=language):
                response = self.post(language=language)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, 'audio/wav')
                self.assertEqual(response.data, self.wav)
                self.assertEqual(response.data[:4], b'RIFF')
                self.assertIn('speech.wav', response.headers['Content-Disposition'])
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
                config = self.config_factory.return_value
                self.assertEqual(config.speech_synthesis_voice_name, voice)
                config.set_speech_synthesis_output_format.assert_called_with(
                    service.speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
                self.config_factory.assert_called_with(subscription='unit-test-placeholder', region='eastus')
                self.synth_factory.assert_called_with(speech_config=config, audio_config=None)
                self.dotenv.assert_called_with(dotenv_path=service.ENV_PATH, override=False)
                self.assertEqual(service.ENV_PATH, Path(service.__file__).resolve().parent / '.env')

    def test_invalid_inputs_do_not_call_service(self):
        cases = [None, [], 'hello', 1, {},
                 {'text': 'ok'}, {'text': None, 'language': 'en-US'},
                 {'text': 4, 'language': 'en-US'},
                 {'text': '', 'language': 'en-US'},
                 {'text': ' \n\t', 'language': 'en-US'},
                 {'text': 'a' * 1001, 'language': 'en-US'},
                 {'text': 'ok', 'language': 'de-DE'},
                 {'text': 'ok', 'language': ['en-US']}]
        for payload in cases:
            with self.subTest(payload=payload):
                response = self.client.post('/api/tts', data=__import__('json').dumps(payload), content_type='application/json')
                self.assertEqual(response.status_code, 400)
                self.assertIsInstance(response.json['error'], str)
        for data, content_type in [('{bad', 'application/json'), ('hello', 'text/plain')]:
            self.assertEqual(self.client.post('/api/tts', data=data, content_type=content_type).status_code, 400)
        self.dotenv.assert_not_called()
        self.synth_factory.assert_not_called()

    def test_1000_characters_allowed(self):
        self.assertEqual(self.post(text='a' * 1000).status_code, 200)

    def test_missing_configuration(self):
        for key, region in [('', ''), ('', 'eastus'), ('unit-test-placeholder', '')]:
            with self.subTest(key_present=bool(key), region_present=bool(region)):
                with patch.dict(os.environ, {'SPEECH_KEY': key, 'SPEECH_REGION': region}, clear=True):
                    response = self.post()
                    self.assertEqual(response.status_code, 503)
                    self.assertIn('SPEECH_KEY', response.json['error'])
        self.config_factory.assert_not_called()
        self.synth_factory.assert_not_called()

    def test_cancellation_errors_are_safe(self):
        codes = service.speechsdk.CancellationErrorCode
        for code, message in [(codes.AuthenticationFailure, 'kimlik'),
                              (codes.TooManyRequests, 'kota'),
                              (codes.ConnectionFailure, 'bağlantı'),
                              (codes.ServiceTimeout, 'zaman'),
                              (codes.ServiceError, 'iptal')]:
            with self.subTest(code=code):
                self.result.reason = service.speechsdk.ResultReason.Canceled
                self.result.cancellation_details = SimpleNamespace(
                    error_code=code, error_details='sensitive-sdk-details')
                response = self.post()
                self.assertEqual(response.status_code, 502)
                self.assertIn(message, response.json['error'])
                self.assertNotIn('sensitive-sdk-details', response.get_data(as_text=True))

    def test_sdk_exception_is_sanitized(self):
        self.synth_factory.side_effect = RuntimeError('sensitive-sdk-details')
        response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn('sensitive-sdk-details', response.get_data(as_text=True))
        self.assertNotIn('unit-test-placeholder', response.get_data(as_text=True))

    def test_incomplete_and_invalid_audio_are_errors(self):
        self.result.reason = service.speechsdk.ResultReason.SynthesizingAudioStarted
        self.assertEqual(self.post().status_code, 502)
        self.result.reason = service.speechsdk.ResultReason.SynthesizingAudioCompleted
        for data in [b'', b'not-a-wav' * 10]:
            self.result.audio_data = data
            self.assertEqual(self.post().status_code, 502)

    def test_unexpected_backend_exception_is_sanitized(self):
        with patch.object(web, 'synthesize_speech', side_effect=RuntimeError('sensitive-details')):
            response = self.post()
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('sensitive-details', response.get_data(as_text=True))

    def test_home_and_static_files_without_settings(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn('Speech Studio', response.get_data(as_text=True))
            for path in ['/static/style.css', '/static/script.js']:
                with self.client.get(path) as static_response:
                    self.assertEqual(static_response.status_code, 200)
        self.dotenv.assert_not_called()
        self.config_factory.assert_not_called()
        self.synth_factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
