
import os
import sys
import json
import time
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

# Agents runtime (Foundry)
from azure.ai.projects import AIProjectClient

# Evaluations (upload to Foundry)
from azure.ai.evaluation import (
    AzureAIProject,
    IntentResolutionEvaluator,
    evaluate
)

# ---------------------------
# Helpers & configuration
# ---------------------------

load_dotenv()

CONN_STR           = os.getenv("AZURE_AI_PROJECT")                 # Foundry Project connection string
AGENT_ID           = os.getenv("AGENT_ID")                         # Existing agent (preferred)
AGENT_MODEL        = os.getenv("AGENT_MODEL", "gpt-4o-mini")
AGENT_NAME         = os.getenv("AGENT_NAME", "tamas-live-test-agent")
AGENT_INSTRUCTIONS = os.getenv("AGENT_INSTRUCTIONS", "You are a helpful assistant for live testing.")

# Evaluator model (Azure OpenAI)
AOAI_ENDPOINT   = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_API_KEY    = os.getenv("AZURE_OPENAI_API_KEY")
AOAI_API_VER    = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
EVAL_DEPLOYMENT = os.getenv("EVAL_MODEL_DEPLOYMENT", "gpt-4o-mini")

if not CONN_STR:
    print("ERROR: AZURE_AI_PROJECT connection string is missing.")
    sys.exit(1)

if not (AOAI_ENDPOINT and AOAI_API_KEY):
    print("ERROR: Azure OpenAI env vars missing (AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY).")
    sys.exit(1)


@dataclass
class Turn:
    user: str
    assistant: str


class LiveAgentTester:
    def __init__(self, conn_str: str):
        self.credential = DefaultAzureCredential()
        self.client = AIProjectClient.from_connection_string(
            conn_str=conn_str,
            credential=self.credential
        )
        self.agent = None
        self.thread = None
        self.transcript: List[Turn] = []

    # ---- Agent setup ----
    def get_or_create_agent(self, agent_id: Optional[str]) -> str:
        if agent_id:
            self.agent = self.client.agents.get(agent_id)
            print(f"[info] Using existing agent: {self.agent.id} ({getattr(self.agent, 'name', '')})")
            return self.agent.id

        # Create a lightweight agent (no tools attached). Prefer using an existing agent with tools.
        self.agent = self.client.agents.create(
            name=AGENT_NAME,
            model=AGENT_MODEL,
            instructions=AGENT_INSTRUCTIONS
        )
        print(f"[info] Created temp agent: {self.agent.id} ({self.agent.name})")
        return self.agent.id

    def create_thread(self) -> str:
        self.thread = self.client.agents.threads.create()
        print(f"[info] Created thread: {self.thread.id}")
        return self.thread.id

    # ---- Messaging ----
    def send_and_receive(self, user_text: str) -> str:
        """
        Try streaming first; on failure fall back to sync.
        Returns assistant final text.
        """
        # 1) Attempt streaming
        try:
            print("[stream] ", end="", flush=True)
            accumulated = []
            with self.client.agents.runs.stream(
                thread_id=self.thread.id,
                agent_id=self.agent.id,
                messages=[{"role": "user", "content": user_text}],
            ) as events:
                for ev in events:
                    # Known streaming types often include token deltas and tool call notifications.
                    etype = getattr(ev, "type", None)
                    if etype == "response.output_text.delta":
                        delta = getattr(ev, "delta", "")
                        accumulated.append(delta)
                        print(delta, end="", flush=True)
                    elif etype == "response.error":
                        err = getattr(ev, "error", "")
                        print(f"\n[error] {err}", flush=True)
                    elif etype and etype.startswith("response.function_call"):
                        # Show tool call events for visibility; the service executes platform tools automatically
                        print(f"\n[tool-call] {getattr(ev, 'arguments', '')}", flush=True)
                print("")  # newline after stream
            return "".join(accumulated) if accumulated else self._get_last_assistant_message_text()
        except Exception as ex:
            print(f"\n[warn] Streaming failed or unavailable, falling back to sync. Reason: {ex}")

        # 2) Sync fallback
        run = self.client.agents.runs.create(
            thread_id=self.thread.id,
            agent_id=self.agent.id,
            messages=[{"role": "user", "content": user_text}],
        )
        # Wait for completion
        self.client.agents.runs.wait(run_id=run.id, thread_id=self.thread.id)

        return self._get_last_assistant_message_text()

    def _get_last_assistant_message_text(self) -> str:
        msgs = list(self.client.agents.threads.list_messages(thread_id=self.thread.id))
        # Get the latest assistant message
        for m in reversed(msgs):
            if getattr(m, "role", "") == "assistant":
                # Some SDKs store content as a list of parts; coalesce to text
                content = getattr(m, "content", "")
                if isinstance(content, list):
                    parts = []
                    for p in content:
                        text = getattr(p, "text", None) or p.get("text") if isinstance(p, dict) else None
                        if text:
                            parts.append(text)
                    return "\n".join(parts)
                return str(content)
        return ""

    # ---- Transcript & persistence ----
    def add_turn(self, user_text: str, assistant_text: str):
        self.transcript.append(Turn(user=user_text, assistant=assistant_text))

    def save_transcript_jsonl(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            for t in self.transcript:
                f.write(json.dumps({"query": t.user, "response": t.assistant}, ensure_ascii=False) + "\n")
        print(f"[info] Transcript saved → {path}")


# ---------------------------
# Evaluation & upload to Foundry
# ---------------------------

def upload_eval_intent_resolution(jsonl_path: str, eval_name: str):
    """
    Reads the transcript JSONL (query/response pairs),
    runs IntentResolutionEvaluator locally,
    and uploads metrics/artifacts into your Foundry project.
    """
    # Bind to Foundry project (important for upload)
    project = AzureAIProject.from_connection_string(os.environ["AZURE_AI_PROJECT"])

    # Azure OpenAI config for evaluator
    model_config = {
        "azure_endpoint":   AOAI_ENDPOINT,
        "api_key":          AOAI_API_KEY,
        "api_version":      AOAI_API_VER,
        "azure_deployment": EVAL_DEPLOYMENT,
    }

    evaluator = IntentResolutionEvaluator(model_config=model_config)

    rows = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    # This runs locally and uploads results to the Foundry project
    result = evaluate(
        data=rows,
        evaluators={"intent_resolution": evaluator},
        azure_ai_project=project,
        evaluation_name=eval_name
    )

    # Print a short summary if available
    try:
        # In many SDK builds, `result` exposes aggregate metrics
        metrics = getattr(result, "metrics", None) or {}
        print("\n[eval] Aggregate metrics:")
        for k, v in metrics.items():
            print(f" - {k}: {v}")
    except Exception:
        pass

    print("[eval] Upload complete. Check your Project → Assess & improve → Evaluation.")


# ---------------------------
# Main (interactive loop)
# ---------------------------

def main():
    print("=== Azure AI Foundry: Live Agent test + IntentResolution evaluation ===")
    tester = LiveAgentTester(CONN_STR)

    # Prepare agent + thread
    agent_id = tester.get_or_create_agent(AGENT_ID)
    tester.create_thread()

    print("\nType your message and press Enter. Type '/exit' to finish and upload evaluation.\n")

    try:
        while True:
            user_text = input("you> ").strip()
            if not user_text:
                continue
            if user_text.lower() in ("/exit", "exit", "quit", "/quit"):
                break

            assistant_text = tester.send_and_receive(user_text)
            if assistant_text:
                print(f"agent> {assistant_text}\n")
            else:
                print("agent> [no text returned]\n")

            tester.add_turn(user_text, assistant_text)

    except KeyboardInterrupt:
        print("\n[info] Interrupted by user.")

    # Save transcript and evaluate
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    jsonl_path = f"transcript_{ts}.jsonl"
    tester.save_transcript_jsonl(jsonl_path)

    eval_name = f"live-intent-resolution-{ts}"
    upload_eval_intent_resolution(jsonl_path, eval_name)

    print("\nAll done.")

if __name__ == "__main__":
    main()
