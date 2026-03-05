# Lab 06: Speech Conversation with Azure AI Foundry

A conversational AI application that supports real-time speech interactions using Azure AI services. Users speak to an AI agent and receive spoken responses, creating a natural voice conversation experience.

## Overview

This lab showcases:

- **Speech-to-Text (STT)**: Convert user speech to text using Azure AI Speech
- **Conversational AI**: Intelligent responses from an agent powered by GPT-4o via Azure AI Foundry
- **Text-to-Speech (TTS)**: Convert agent responses to natural-sounding speech
- **Real-time Audio**: Seamless audio capture and playback in a Streamlit web interface
- **Azure Developer CLI**: One-command infrastructure provisioning with `azd`

## Architecture

```
User speaks → [Streamlit Frontend] → Azure Speech STT → Transcribed Text
                                                            │
                                                            ▼
                                                     Azure OpenAI (GPT-4o)
                                                            │
                                                            ▼
User hears  ← [Streamlit Frontend] ← Azure Speech TTS ← Agent Response
```

All processing (speech recognition, agent logic, speech synthesis) runs in a single
Streamlit application that connects to Azure services for the heavy lifting.

## Prerequisites

- **Azure Subscription** with Owner or Contributor access
- **Azure Developer CLI (azd)** — [Install here](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- **Azure CLI** — [Install here](https://learn.microsoft.com/cli/azure/install-azure-cli)
- **Python 3.11+**

## Quick Start

```bash
cd labs/lab06-speech-conversation

# 1. Authenticate
azd auth login
az login

# 2. Provision Azure resources
azd up

# 3. Export environment to .env
azd env get-values > .env

# 4. Install Python dependencies
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r src/requirements.txt

# 5. Run the application
cd src
streamlit run app.py
```

Open `http://localhost:8501`, click the microphone, and start talking!

## Azure Services Provisioned

| Service | Purpose | SKU |
|---------|---------|-----|
| **Azure AI Foundry** | Hosts AI project and GPT-4o model | S0 |
| **Azure OpenAI (GPT-4o)** | Powers the conversational agent | Global Standard |
| **Azure AI Speech** | Speech-to-text and text-to-speech | S0 |
| **Log Analytics** | Monitoring and diagnostics | Per-GB |

**Estimated cost**: ~$5/month base + pay-per-use for Speech and OpenAI tokens.

## Project Structure

```
lab06-speech-conversation/
├── infra/                          # Bicep infrastructure templates
│   ├── main.bicep                  # Main orchestration
│   ├── main.parameters.json        # Parameter file for azd
│   ├── abbreviations.json          # Resource naming prefixes
│   └── modules/
│       ├── ai-project.bicep        # AI Foundry + Project + GPT-4o
│       ├── speech.bicep            # Azure Speech Service
│       ├── log-analytics.bicep     # Log Analytics workspace
│       └── role-assignment.bicep   # RBAC role assignment helper
├── src/                            # Application source code
│   ├── app.py                      # Streamlit UI (main entry point)
│   ├── speech_client.py            # Azure Speech SDK wrapper (STT/TTS)
│   ├── agent.py                    # Conversational agent (Azure OpenAI)
│   ├── config.py                   # Configuration management
│   ├── requirements.txt            # Python dependencies
│   └── Dockerfile                  # Container image (optional)
├── azure.yaml                      # Azure Developer CLI config
├── .env.example                    # Environment variable template
├── .gitignore
├── QUICKSTART.md                   # Step-by-step guide
└── README.md                       # This file
```

## How It Works

### 1. Voice Capture
The Streamlit frontend uses the `audio-recorder-streamlit` component to capture
audio from the browser microphone. Clicking the microphone icon starts recording;
silence automatically stops it.

### 2. Speech-to-Text
Captured audio (WAV) is sent to Azure AI Speech for transcription. The SDK
handles noise reduction, language detection, and accurate transcription.

### 3. Agent Processing
The transcribed text is appended to the conversation history and sent to
Azure OpenAI (GPT-4o). The agent maintains context across turns, creating
a natural dialogue flow.

### 4. Text-to-Speech
The agent's text response is synthesized into natural-sounding speech using
Azure AI Speech neural voices. Multiple voice options are available in the
sidebar settings.

### 5. Audio Playback
The synthesized audio plays automatically in the browser, completing the
conversation loop. A text input fallback is also available.

## Local Development

### Authentication

The application uses two authentication methods:

| Service | Auth Method | Configuration |
|---------|-------------|---------------|
| Azure OpenAI | `DefaultAzureCredential` | Automatic via `az login` |
| Azure Speech | Key-based (default) | `AZURE_SPEECH_KEY` env var |
| Azure Speech | Token-based (optional) | `AZURE_SPEECH_ENDPOINT` + `az login` |

For local development, `az login` is sufficient. The Speech key is
automatically output by `azd provision`.

### Environment Variables

After provisioning, export variables with:

```bash
azd env get-values > .env
```

Or copy `.env.example` to `.env` and fill in manually.

### Running

```bash
cd src
streamlit run app.py
```

The app starts at `http://localhost:8501`.

## Customisation

### Change the Voice

Select a different neural voice from the sidebar dropdown, or set the
`SPEECH_VOICE` environment variable. See [available voices](https://learn.microsoft.com/azure/ai-services/speech-service/language-support?tabs=tts).

### Change the Language

Set `SPEECH_LANGUAGE` in your `.env` file (e.g., `fr-FR`, `de-DE`, `ja-JP`).

### Modify the Agent Personality

Edit the `SYSTEM_PROMPT` in `src/agent.py` to change how the agent behaves
and responds.

## Troubleshooting

### "Configuration errors" on startup

Run `azd env get-values > .env` to ensure environment variables are set.

### Microphone not working

- Allow microphone permissions in your browser
- Use Chrome or Edge for best WebRTC compatibility
- Check system audio settings

### "No speech detected"

- Speak clearly and close to the microphone
- Wait for the recording indicator before speaking
- Check that pause_threshold in `app.py` isn't too short

### Authentication errors

```bash
az login
azd auth login
```

### Speech SDK errors on Linux

Install system dependencies:
```bash
sudo apt-get install -y libssl-dev libasound2
```

## Next Steps

- Add multi-language support with automatic language detection
- Implement streaming STT for real-time transcription display
- Add conversation export (save/load history)
- Deploy to Azure Container Apps for cloud hosting
- Add Application Insights telemetry

## License

MIT — see the repository [LICENSE](../../LICENSE) file.
