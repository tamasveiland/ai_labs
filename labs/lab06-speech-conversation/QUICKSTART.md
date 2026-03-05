# Quickstart: Speech Conversation Lab

Step-by-step guide to get the lab running in under 10 minutes.

## Step 1 — Install tools

| Tool | Install |
|------|---------|
| Azure CLI | `winget install Microsoft.AzureCLI` |
| Azure Developer CLI | `winget install Microsoft.Azd` |
| Python 3.11+ | `winget install Python.Python.3.11` |

## Step 2 — Authenticate

```bash
az login
azd auth login
```

## Step 3 — Provision Azure resources

```bash
cd labs/lab06-speech-conversation
azd up
```

You will be prompted for:
- **Environment name** — e.g. `lab06-dev`
- **Azure location** — e.g. `eastus2` (must support Speech and OpenAI)
- **Azure subscription** — select your subscription

This takes approximately 3-5 minutes and creates:
- AI Foundry resource with GPT-4o model deployment
- Azure Speech Service
- Log Analytics workspace
- RBAC role assignments for your user

## Step 4 — Export configuration

```bash
azd env get-values > .env
```

This writes all Azure resource endpoints and keys to a `.env` file that the
application reads automatically.

## Step 5 — Create Python virtual environment

```bash
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# macOS / Linux:
source .venv/bin/activate
```

## Step 6 — Install dependencies

```bash
pip install -r src/requirements.txt
```

> **Note (Linux/WSL):** The Azure Speech SDK requires system packages:
> `sudo apt-get install -y libssl-dev libasound2`

## Step 7 — Run the application

```bash
cd src
streamlit run app.py
```

The application opens at **http://localhost:8501**.

## Step 8 — Have a conversation!

1. Click the **microphone icon** to start recording
2. **Speak** your message (silence auto-stops recording)
3. Watch the transcription appear as a chat bubble
4. The agent's text response appears below
5. The response is **spoken aloud** automatically
6. Repeat!

You can also type in the text box at the bottom as a fallback.

## Step 9 — Clean up (when done)

```bash
azd down
```

This deletes all Azure resources created by the lab.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `AZURE_SPEECH_KEY is required` | Run `azd env get-values > .env` |
| Microphone not detected | Allow mic permissions in browser settings |
| `az login` expired | Run `az login` again |
| Speech SDK import error | `pip install azure-cognitiveservices-speech` |
| Port 8501 in use | `streamlit run app.py --server.port 8502` |
