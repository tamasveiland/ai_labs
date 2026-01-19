# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    Given an AIProjectClient, this sample demonstrates how to use the synchronous
    `openai.evals.*` methods to create, get and list evaluation and eval runs for
    Intent Resolution evaluator using inline dataset content.

USAGE:
    python sample_intent_resolution.py

    Before running the sample:

    pip install "azure-ai-projects>=2.0.0b1" python-dotenv

    Set these environment variables with your own values:
    1) AZURE_AI_PROJECT_ENDPOINT - Required. The Azure AI Project endpoint, as found in the overview page of your
       Microsoft Foundry project. It has the form: https://<account_name>.services.ai.azure.com/api/projects/<project_name>.
    2) AZURE_AI_MODEL_DEPLOYMENT_NAME - Required. The name of the model deployment to use for evaluation.
"""

from dotenv import load_dotenv
import os
import json
import time
from pprint import pprint

from azure.identity import DefaultAzureCredential, ChainedTokenCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents import AgentsClient
from azure.ai.evaluation import IntentResolutionEvaluator, evaluate, AzureAIProject
from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam,
    SourceFileContent,
    SourceFileContentContent,
)
from dataclasses import dataclass
from typing import List
from openai.types.eval_create_params import DataSourceConfigCustom


load_dotenv()


@dataclass
class Turn:
    user: str
    assistant: str


def _get_last_assistant_message_text(agents_client, thread_id) -> str:
    msgs = list(agents_client.threads.list_messages(thread_id=thread_id))
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


def save_transcript_jsonl(transcript: List[Turn], path: str):
        with open(path, "w", encoding="utf-8") as f:
            for t in transcript:
                f.write(json.dumps({"query": t.user, "response": t.assistant}, ensure_ascii=False) + "\n")
        print(f"[info] Transcript saved → {path}")


def upload_eval_intent_resolution(project: AzureAIProject, model_config, credential: ChainedTokenCredential, jsonl_path: str, eval_name: str):
    """
    Reads the transcript JSONL (query/response pairs),
    runs IntentResolutionEvaluator locally,
    and uploads metrics/artifacts into your Foundry project.
    """


    evaluator = IntentResolutionEvaluator(model_config=model_config, threshold=3, credential=credential)

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




def main() -> None:
    endpoint = os.environ[
        "AZURE_AI_PROJECT_ENDPOINT"
    ]  # Sample : https://<account_name>.services.ai.azure.com/api/projects/<project_name>
    model_deployment_name = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "")  # Sample : gpt-4o-mini

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential, api_version="2025-11-15-preview") as project_client,
        AgentsClient(endpoint=endpoint, credential=credential, api_version="2025-11-15-preview") as agents_client,
        #AzureAIProject.from_connection_string(endpoint) as project,
        project_client.get_openai_client() as client,
    ):

        project= os.environ["AZURE_AI_PROJECT_ENDPOINT"]

        # Azure OpenAI config for evaluator
        model_config = {
            "azure_endpoint":   os.environ["AZURE_OPENAI_ENDPOINT"],
            "api_version":      os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
            "azure_deployment": os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        }

        # Load data from file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(script_dir, "intent_resolution_test_data.jsonl")
        print(f"\n📂 Loading: {data_file}")
        test_data = []
        with open(data_file, "r") as f:
            for line in f:
                test_data.append(json.loads(line))
        print(f"✅ Loaded {len(test_data)} test cases\n")


        # Get the agent
        agent = project_client.agents.get_version(agent_name="customer-service-agent-live-eval", agent_version="5")
        
        transcript: List[Turn] = []
        # iterate over test data and create a thread for each
        for entry in test_data:
            query = entry.get("query", "")
            response = entry.get("response", "")
            tool_definitions = entry.get("tool_definitions")

            print(f"\n📄 Creating thread for query: {query[:60]}...")

            # Create a new
            thread = agents_client.threads.create()
            run = agents_client.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id,
                additional_messages={
                    "role": "USER", 
                    "content": query
                    }
            )

            agents_client.agents.runs.wait(run_id=run.id, thread_id=thread.id)

            assistant_text = _get_last_assistant_message_text(agents_client, thread.id)

            transcript.append(Turn(user=query, assistant=assistant_text))



        # Save transcript and evaluate
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        jsonl_path = f"transcript_{ts}.jsonl"
        save_transcript_jsonl(transcript, jsonl_path)

        print("Creating Eval Run with live agent responses...")

        
        eval_name = f"live-intent-resolution-{ts}"
            # Azure OpenAI config for evaluator

        upload_eval_intent_resolution(project, model_config, credential, jsonl_path, eval_name)

        print("\nAll done.")


 


if __name__ == "__main__":
    main()
