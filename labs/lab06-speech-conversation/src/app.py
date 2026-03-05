"""
Speech Conversation with Azure AI Foundry — Streamlit Frontend.

A conversational AI application that captures speech, transcribes it,
sends it to a GPT-4o agent, and plays back the spoken response.
"""

import hashlib
import logging
import time

import streamlit as st
from audio_recorder_streamlit import audio_recorder

from agent import ConversationalAgent
from config import Config
from speech_client import DEFAULT_VOICES, SpeechClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Voice Conversation — Azure AI",
    page_icon="🎤",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Load configuration & validate
# ---------------------------------------------------------------------------
config = Config.from_env()
errors = config.validate()
if errors:
    st.error("**Configuration errors:**\n" + "\n".join(f"- {e}" for e in errors))
    st.info(
        "Run `azd provision` to create Azure resources, then "
        "`azd env get-values > .env` to populate your local environment."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Initialise session state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "speech_client" not in st.session_state:
    st.session_state.speech_client = SpeechClient(config)
if "agent" not in st.session_state:
    st.session_state.agent = ConversationalAgent(config)
if "processed_hashes" not in st.session_state:
    st.session_state.processed_hashes = set()
if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None
if "detected_language" not in st.session_state:
    st.session_state.detected_language = None
if "metrics" not in st.session_state:
    st.session_state.metrics = None

# ---------------------------------------------------------------------------
# Sidebar — Settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    auto_detect = st.checkbox(
        "Auto-detect language",
        value=True,
        help="Automatically detect the spoken language (English / Hungarian).",
        key="auto_detect_lang",
    )
    config.auto_detect_language = auto_detect

    voice = st.selectbox(
        "Assistant voice",
        [
            "en-US-JennyNeural",
            "en-US-GuyNeural",
            "en-US-AriaNeural",
            "en-US-DavisNeural",
            "en-US-SaraNeural",
            "en-GB-SoniaNeural",
            "hu-HU-NoemiNeural",
            "hu-HU-TamasNeural",
        ],
        index=0,
        disabled=auto_detect,
        help="Ignored when auto-detect is on — voice is chosen from detected language.",
        key="voice_select",
    )
    # Derive recognition language from the voice locale (e.g. "hu-HU-NoemiNeural" → "hu-HU")
    derived_language = "-".join(voice.split("-")[:2])

    # Update config if voice or language changed
    if not auto_detect and (
        voice != config.speech_voice or derived_language != config.speech_language
    ):
        config.speech_voice = voice
        config.speech_language = derived_language
        st.session_state.speech_client = SpeechClient(config)

    # Always keep the session-state client in sync with the current config
    # (Streamlit re-runs create a fresh config each time).
    st.session_state.speech_client.config = config

    # Show current / detected language
    if auto_detect:
        detected = st.session_state.detected_language
        if detected:
            st.info(f"🌐 Detected language: **{detected}**")
        else:
            st.caption("🌐 Language: _waiting for speech…_")
    else:
        st.caption(f"🌐 Language: **{derived_language}**")

    # --- Performance metrics section ---
    st.divider()
    st.subheader("📊 Last Turn Metrics")
    m = st.session_state.metrics

    def _fmt(value, fmt=".2f", suffix="s"):
        """Format a metric value, or return '-' if unavailable."""
        if m is None or value is None:
            return "\u2013"
        return f"{value:{fmt}} {suffix}" if suffix else f"{value:{fmt}}"

    def _fmt_int(value):
        if m is None or value is None:
            return "\u2013"
        return str(value)

    st.markdown(
        f"**Input speech length:** {_fmt(m and m.get('input_audio_duration'), '.1f')}\n\n"
        f"**Speech-to-text duration:** {_fmt(m and m.get('stt_duration'))}\n\n"
        f"**Input tokens (prompt):** {_fmt_int(m and m.get('prompt_tokens'))}\n\n"
        f"**Output tokens (completion):** {_fmt_int(m and m.get('completion_tokens'))}\n\n"
        f"**Agent thinking duration:** {_fmt(m and m.get('agent_duration'))}\n\n"
        f"**Text-to-speech duration:** {_fmt(m and m.get('tts_duration'))}\n\n"
        f"**Total response latency:** {_fmt(m and m.get('total_latency'))}"
    )

    st.divider()

    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent.reset()
        st.session_state.processed_hashes = set()
        st.session_state.pending_audio = None
        st.session_state.detected_language = None
        st.session_state.metrics = None
        st.rerun()

    st.divider()
    st.caption("Powered by Azure AI Speech & Azure OpenAI")
    st.caption(f"Region: `{config.speech_region}`")
    st.caption(f"Model: `{config.openai_deployment}`")

# ---------------------------------------------------------------------------
# Title & Instructions
# ---------------------------------------------------------------------------
st.title("🎤 Voice Conversation")
st.markdown(
    "Click the microphone below to speak. The AI will listen, think, "
    "and respond with voice."
)

# ---------------------------------------------------------------------------
# Voice input (audio recorder widget)
# ---------------------------------------------------------------------------
audio_bytes = audio_recorder(
    text="",
    recording_color="#e74c3c",
    neutral_color="#6c757d",
    icon_name="microphone",
    icon_size="3x",
    pause_threshold=2.5,
    sample_rate=44100,
    key="audio_recorder",
)

# ---------------------------------------------------------------------------
# Display conversation history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------------------------------------------------------------------
# Play pending audio from previous processing cycle
# ---------------------------------------------------------------------------
if st.session_state.pending_audio is not None:
    st.audio(st.session_state.pending_audio, format="audio/wav", autoplay=True)
    st.session_state.pending_audio = None

# ---------------------------------------------------------------------------
# Process newly recorded audio
# ---------------------------------------------------------------------------
if audio_bytes:
    audio_hash = hashlib.md5(audio_bytes).hexdigest()

    if audio_hash not in st.session_state.processed_hashes:
        st.session_state.processed_hashes.add(audio_hash)

        # --- Speech-to-Text ---------------------------------------------------
        with st.spinner("🎧 Transcribing your speech..."):
            t_stt_start = time.perf_counter()
            user_text = st.session_state.speech_client.speech_to_text(audio_bytes)
            t_stt_end = time.perf_counter()
            # Persist detected language in session state so it survives client recreation
            if st.session_state.speech_client.detected_language:
                st.session_state.detected_language = (
                    st.session_state.speech_client.detected_language
                )

        # Estimate input audio duration from WAV byte length
        # (16-bit mono @ 44 100 Hz → 88 200 bytes / second)
        input_audio_duration = max(len(audio_bytes) - 44, 0) / 88200

        if user_text and not user_text.startswith("["):
            # Show user message
            st.session_state.messages.append(
                {"role": "user", "content": user_text}
            )
            with st.chat_message("user"):
                st.write(user_text)

            # --- Agent Response ------------------------------------------------
            with st.spinner("🤔 Thinking..."):
                t_agent_start = time.perf_counter()
                chat_result = st.session_state.agent.chat(user_text)
                t_agent_end = time.perf_counter()
                response_text = chat_result.text

            st.session_state.messages.append(
                {"role": "assistant", "content": response_text}
            )
            with st.chat_message("assistant"):
                st.write(response_text)

            # --- Text-to-Speech ------------------------------------------------
            with st.spinner("🔊 Generating speech..."):
                t_tts_start = time.perf_counter()
                # When auto-detect is on, pick voice matching detected language
                speech_client = st.session_state.speech_client
                detected = st.session_state.detected_language
                if config.auto_detect_language and detected:
                    config.speech_voice = DEFAULT_VOICES.get(
                        detected, config.speech_voice
                    )
                    config.speech_language = detected
                    # Refresh client so TTS uses the right voice
                    speech_client = SpeechClient(config)
                    st.session_state.speech_client = speech_client

                audio_response = speech_client.text_to_speech(
                    response_text
                )
                t_tts_end = time.perf_counter()

            # Store metrics for sidebar display
            st.session_state.metrics = {
                "input_audio_duration": input_audio_duration,
                "stt_duration": t_stt_end - t_stt_start,
                "prompt_tokens": chat_result.prompt_tokens,
                "completion_tokens": chat_result.completion_tokens,
                "agent_duration": t_agent_end - t_agent_start,
                "tts_duration": t_tts_end - t_tts_start,
                "total_latency": t_tts_end - t_stt_end,
            }

            if audio_response:
                st.session_state.pending_audio = audio_response
            else:
                st.warning("Could not generate speech for the response.")

            # Rerun so sidebar metrics refresh immediately
            st.rerun()
        else:
            st.warning(
                "Could not understand the audio. Please try speaking again."
            )

# ---------------------------------------------------------------------------
# Text input fallback
# ---------------------------------------------------------------------------
st.divider()
text_input = st.chat_input("Or type a message...")

if text_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": text_input})

    # Get agent response
    t_agent_start = time.perf_counter()
    chat_result = st.session_state.agent.chat(text_input)
    t_agent_end = time.perf_counter()
    response_text = chat_result.text
    st.session_state.messages.append(
        {"role": "assistant", "content": response_text}
    )

    # Generate speech for the response
    t_tts_start = time.perf_counter()
    audio_response = st.session_state.speech_client.text_to_speech(response_text)
    t_tts_end = time.perf_counter()
    if audio_response:
        st.session_state.pending_audio = audio_response

    st.session_state.metrics = {
        "input_audio_duration": 0,
        "stt_duration": 0,
        "prompt_tokens": chat_result.prompt_tokens,
        "completion_tokens": chat_result.completion_tokens,
        "agent_duration": t_agent_end - t_agent_start,
        "tts_duration": t_tts_end - t_tts_start,
        "total_latency": t_tts_end - t_agent_start,
    }

    st.rerun()
