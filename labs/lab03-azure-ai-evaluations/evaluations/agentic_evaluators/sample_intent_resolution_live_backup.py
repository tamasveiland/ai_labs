# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    Given an AIProjectClient, this sample demonstrates how to use the synchronous
    `openai.evals.*` methods to create, get and list evaluation and eval runs for
    Intent Resolution evaluator with LIVE agent execution.
    
    Unlike the inline data sample, this creates an agent that runs LIVE during evaluation,
    making real tool calls and generating responses in real-time.

USAGE:
    python sample_intent_resolution_live.py

    Before running the sample:

    pip install "azure-ai-projects>=2.0.0b1" python-dotenv

    Set these environment variables with your own values:
    1) AZURE_AI_PROJECT_ENDPOINT - Required. The Azure AI Project endpoint, as found in the overview page of your
       Microsoft Foundry project. It has the form: https://<account_name>.services.ai.azure.com/api/projects/<project_name>.
    2) AZURE_AI_MODEL_DEPLOYMENT_NAME - Required. The name of the model deployment to use for evaluation.
"""

from datetime import datetime
from dotenv import load_dotenv
import os
import time
from pprint import pprint

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    DatasetVersion,
)
from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam,
    SourceFileID
)
from azure.ai.evaluation import IntentResolutionEvaluator

load_dotenv()

def main() -> None:
    endpoint = os.environ[
        "AZURE_AI_PROJECT_ENDPOINT"
    ]  # Sample : https://<account_name>.services.ai.azure.com/api/projects/<project_name>

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential, api_version="2025-11-15-preview") as project_client,
        project_client.get_openai_client() as client,
    ):

        # # Construct the paths to the data folder and data file used in this sample
        # script_dir = os.path.dirname(os.path.abspath(__file__))
        # data_file = os.path.join(script_dir, "intent_resolution_test_data.jsonl")

        # print("Upload a single file and create a new Dataset to reference the file.")
        # dataset: DatasetVersion = project_client.datasets.upload_file(
        #     name=f"agent-test-data-{datetime.utcnow().strftime('%Y-%m-%d_%H%M%S_UTC')}",
        #     version="1",
        #     file_path=data_file,
        # )
        # pprint(dataset)

        print("\nRetrieving Dataset ...")
        dataset: DatasetVersion = project_client.datasets.get(name="agent_test_data", version="1")
        print(f"✅ Dataset retrieved: {dataset.id}\n")
        # print(f"✅ Dataset retrieved: {dataset.data_uri}\n")
        # print(f"✅ Dataset retrieved: {dataset.name}\n")

        print("Retrieving Evaluation with live agent target...")

        eval_retrieve_response = client.evals.retrieve("eval_ccc44bad95794afe9ebffbcf7947673c")
        print(f"✅ Evaluation retrieved: {eval_retrieve_response.id}\n")

        # print("Creating Eval Run with live agent responses...")
        # eval_run_object = client.evals.runs.create(
        #     eval_id=eval_retrieve_response.id,
        #     name="live_agent_run_local",
        #     metadata={"team": "data-science-unit", "scenario": "live-agent-local"},
        #     data_source=CreateEvalJSONLRunDataSourceParam(
        #         type="jsonl",
        #         source=SourceFileID(type="file_id", id=dataset.id)
        #     )
        # )

        eval_run_object = client.evals.runs.create(
            eval_id=eval_retrieve_response.id,
            name="live_agent_run_local",


        # print(f"✅ Eval Run created: {eval_run_object.id}")
        # print("🔄 Agent is now running live for each test query...")
        # pprint(eval_run_object)

        # print("\n\n----Waiting for Live Eval Run to Complete----\n")

        # while True:
        #     run = client.evals.runs.retrieve(run_id=eval_run_object.id, eval_id=eval_retrieve_response.id)
        #     print(f"Status: {run.status}")
            
        #     if run.status == "completed" or run.status == "failed":
        #         print("\n" + "="*80)
        #         print("EVALUATION RESULTS")
        #         print("="*80)
                
        #         output_items = list(client.evals.runs.output_items.list(run_id=run.id, eval_id=eval_retrieve_response.id))
                
        #         for i, item in enumerate(output_items, 1):
        #             print(f"\n--- Test Case {i} ---")
        #             if hasattr(item, 'input') and item.input:
        #                 print(f"Query: {item.input.get('query', 'N/A')}")
        #             if hasattr(item, 'output') and item.output:
        #                 print(f"Agent Response: {item.output.get('response', 'N/A')[:200]}...")
        #             if hasattr(item, 'scores'):
        #                 print(f"Intent Resolution Score: {item.scores}")
        #             print()
                
        #         print(f"✅ Eval Run Status: {run.status}")
        #         print(f"📊 Eval Run Report URL: {run.report_url}")
        #         print("="*80)
        #         break
                
        #     time.sleep(5)
        #     print("⏳ Waiting for eval run to complete...")



if __name__ == "__main__":
    main()
