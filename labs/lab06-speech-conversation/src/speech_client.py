"""Azure Speech SDK wrapper for Speech-to-Text and Text-to-Speech.

Supports two authentication modes:
  1. Key-based auth: Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION
  2. Token-based auth (Entra ID): Set AZURE_SPEECH_ENDPOINT and AZURE_SPEECH_REGION
     Requires `az login` locally or managed identity in production.
"""

import logging
import os
import tempfile

import azure.cognitiveservices.speech as speechsdk

from config import Config

logger = logging.getLogger(__name__)


# Map language locale to a default TTS voice for auto-detect mode
DEFAULT_VOICES: dict[str, str] = {
    "en-US": "en-US-JennyNeural",
    "en-GB": "en-GB-SoniaNeural",
    "hu-HU": "hu-HU-NoemiNeural",
}


class SpeechClient:
    """Handles Speech-to-Text and Text-to-Speech using Azure Speech SDK."""

    def __init__(self, config: Config):
        self.config = config
        self._credential = None
        self.detected_language: str | None = None

        # Validate minimum config
        if not config.speech_key and not config.speech_endpoint:
            raise ValueError(
                "Either AZURE_SPEECH_KEY or AZURE_SPEECH_ENDPOINT must be set."
            )

    def _get_speech_config(self) -> speechsdk.SpeechConfig:
        """Create a fresh SpeechConfig with appropriate auth.

        Creates a new config each time to handle token expiration gracefully.
        """
        if self.config.speech_key:
            # Key-based authentication (simplest for local dev)
            speech_config = speechsdk.SpeechConfig(
                subscription=self.config.speech_key,
                region=self.config.speech_region,
            )
        else:
            # Token-based authentication via DefaultAzureCredential
            from azure.identity import DefaultAzureCredential

            if self._credential is None:
                self._credential = DefaultAzureCredential()

            token = self._credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )

            # For resources with custom domain, use aad#resource_id#token format
            if self.config.speech_resource_id:
                auth_token = (
                    f"aad#{self.config.speech_resource_id}#{token.token}"
                )
            else:
                auth_token = token.token

            speech_config = speechsdk.SpeechConfig(
                auth_token=auth_token,
                region=self.config.speech_region,
            )

        # Configure language settings
        # Skip setting recognition language when auto-detect is active;
        # it conflicts with AutoDetectSourceLanguageConfig.
        if not self.config.auto_detect_language:
            speech_config.speech_recognition_language = self.config.speech_language
        speech_config.speech_synthesis_voice_name = self.config.speech_voice

        return speech_config

    def speech_to_text(self, audio_bytes: bytes) -> str:
        """Convert audio bytes (WAV format) to text.

        Args:
            audio_bytes: Raw WAV audio data from the microphone.

        Returns:
            Transcribed text, or an error message prefixed with '['.
        """
        # Write audio to a temporary WAV file for the SDK
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        try:
            speech_config = self._get_speech_config()
            audio_config = speechsdk.AudioConfig(filename=temp_path)

            if self.config.auto_detect_language:
                auto_detect_config = (
                    speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                        languages=self.config.candidate_languages
                    )
                )
                recognizer = speechsdk.SpeechRecognizer(
                    speech_config=speech_config,
                    audio_config=audio_config,
                    auto_detect_source_language_config=auto_detect_config,
                )
            else:
                recognizer = speechsdk.SpeechRecognizer(
                    speech_config=speech_config,
                    audio_config=audio_config,
                )

            # Perform single-shot recognition
            result = recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # Store detected language for TTS voice selection
                if self.config.auto_detect_language:
                    auto_detect_result = speechsdk.AutoDetectSourceLanguageResult(result)
                    self.detected_language = auto_detect_result.language
                    logger.info("Detected language: %s", self.detected_language)
                logger.info("STT result: %s", result.text)
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech recognized in audio")
                return "[No speech detected. Please try again.]"
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(
                    "STT canceled: %s - %s",
                    cancellation.reason,
                    cancellation.error_details,
                )
                return f"[Speech recognition error: {cancellation.reason}]"
            else:
                return f"[Unexpected result: {result.reason}]"

        except Exception as e:
            logger.exception("Speech-to-text failed")
            return f"[STT Error: {e}]"

        finally:
            # On Windows the Speech SDK may still hold the file handle after
            # recognize_once() returns.  Retry the delete briefly, then give up
            # silently so the PermissionError doesn't mask the STT result.
            import time

            for attempt in range(5):
                try:
                    os.unlink(temp_path)
                    break
                except PermissionError:
                    if attempt < 4:
                        time.sleep(0.2)
                    else:
                        logger.warning(
                            "Could not delete temp file %s — "
                            "the Speech SDK may still hold the handle.",
                            temp_path,
                        )

    def text_to_speech(self, text: str) -> bytes | None:
        """Convert text to audio bytes (WAV format).

        Args:
            text: The text to synthesize as speech.

        Returns:
            WAV audio bytes, or None if synthesis fails.
        """
        try:
            speech_config = self._get_speech_config()

            # Configure output format for high-quality audio
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
            )

            # Synthesize without audio output device (we want the bytes)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=None,
            )

            result = synthesizer.speak_text(text)

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("TTS completed: %d bytes", len(result.audio_data))
                return result.audio_data
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(
                    "TTS canceled: %s - %s",
                    cancellation.reason,
                    cancellation.error_details,
                )
                return None
            else:
                logger.error("TTS unexpected result: %s", result.reason)
                return None

        except Exception as e:
            logger.exception("Text-to-speech failed")
            return None
