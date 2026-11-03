"""Offline TTS tests using the installed SDK surface; no dotenv or Azure I/O."""
import os
import time
import unittest
from unittest.mock import create_autospec, patch

import speech_service as s
from app import app
from test_voice import wav


class TtsTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.addCleanup(patch.stopall)
        self.dotenv = patch.object(s, 'load_dotenv').start()
        patch.dict(os.environ, {'SPEECH_KEY': 'test-placeholder', 'SPEECH_REGION': 'eastus'}).start()
        self.config = patch.object(s.speechsdk, 'SpeechConfig', autospec=True).start()
        self.synth = create_autospec(s.speechsdk.SpeechSynthesizer, instance=True, spec_set=True)
        self.constructor = patch.object(s.speechsdk, 'SpeechSynthesizer', return_value=self.synth).start()
        self.result = create_autospec(s.speechsdk.SpeechSynthesisResult, instance=True, spec_set=True)
        self.result.reason = s.speechsdk.ResultReason.SynthesizingAudioCompleted
        self.result.audio_data = wav()
        self.synth.speak_text_async.return_value.get.return_value = self.result

    def post(self, text='Successfully deleted item 4.'):
        return self.client.post('/api/tts', json={'text': text})

    def reusable(self):
        self.assertTrue(s._speech_lock.acquire(blocking=False))
        s._speech_lock.release()

    def test_wav_plain_text_format_and_server_speaker_disabled(self):
        text = "Successfully created book '<speak>Title</speak>' with ID 4."
        response = self.post(text)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'audio/wav')
        self.assertEqual(response.data, wav())
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.synth.speak_text_async.assert_called_once_with(text)
        self.synth.speak_ssml_async.assert_not_called()
        self.constructor.assert_called_once_with(speech_config=self.config.return_value, audio_config=None)
        self.config.return_value.set_speech_synthesis_output_format.assert_called_once_with(
            s.speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
        self.assertEqual(self.config.return_value.speech_synthesis_voice_name, 'en-US-JennyNeural')
        self.dotenv.assert_called_once_with(dotenv_path=s.ENV_PATH, override=False)
        self.synth.stop_speaking_async.assert_called_once()
        self.reusable()

    def test_invalid_text_and_json_do_not_load_settings(self):
        for text in ['', '  ', None, 4, [], 'x' * 2001]:
            self.assertEqual(self.post(text).status_code, 400)
        for body in [[], {}, {'text': 'hello', 'voice': 'other'}]:
            self.assertEqual(self.client.post('/api/tts', json=body).status_code, 400)
        self.assertEqual(self.client.post('/api/tts', data='{', content_type='application/json').status_code, 400)
        self.dotenv.assert_not_called()

    def test_limit_and_oversize_body(self):
        self.assertEqual(self.post('x' * 2000).status_code, 200)
        self.assertEqual(self.post('x' * 20000).status_code, 413)
        self.reusable()

    def test_missing_settings_keeps_page_and_library_available(self):
        with patch.dict(os.environ, {'SPEECH_KEY': '', 'SPEECH_REGION': ''}):
            self.assertEqual(self.post().status_code, 503)
            self.assertEqual(self.client.get('/').status_code, 200)
            self.assertEqual(self.client.get('/api/items').status_code, 200)
        self.reusable()

    def test_canceled_empty_or_unexpected_result_is_not_success(self):
        for reason, data in [(s.speechsdk.ResultReason.Canceled, b''),
                             (s.speechsdk.ResultReason.SynthesizingAudioCompleted, b''),
                             (s.speechsdk.ResultReason.SynthesizingAudio, wav())]:
            self.result.reason, self.result.audio_data = reason, data
            response = self.post()
            self.assertEqual(response.status_code, 502)
            self.assertIn('error', response.json)
            self.reusable()

    def test_native_error_is_sanitized_and_lock_reusable(self):
        for error in [RuntimeError('secret native diagnostics'), ValueError('secret SDK arguments')]:
            self.synth.speak_text_async.side_effect = error
            response = self.post()
            self.assertEqual(response.status_code, 502)
            self.assertNotIn('secret', response.get_data(as_text=True))
            self.reusable()
        self.synth.speak_text_async.side_effect = None
        self.assertEqual(self.post().status_code, 200)

    def test_timeout_and_stop_cleanup(self):
        self.synth.speak_text_async.return_value.get.side_effect = lambda: time.sleep(0.05)
        with patch.object(s, 'TTS_TIMEOUT_SECONDS', 0.001):
            self.assertEqual(self.post().status_code, 502)
        self.synth.stop_speaking_async.assert_called_once()
        self.reusable()

    def test_cleanup_failure_cannot_return_success_or_mask_primary(self):
        self.synth.stop_speaking_async.side_effect = RuntimeError('hidden cleanup')
        self.assertEqual(self.post().status_code, 502)
        self.reusable()
        self.synth.speak_text_async.side_effect = RuntimeError('hidden primary')
        response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertIn('could not be completed', response.json['error'])
        self.assertNotIn('hidden', response.get_data(as_text=True))
        self.reusable()

    def test_busy_does_not_touch_azure(self):
        s._speech_lock.acquire()
        try:
            self.assertEqual(self.post().status_code, 502)
            self.dotenv.assert_not_called()
        finally:
            s._speech_lock.release()
        self.reusable()
