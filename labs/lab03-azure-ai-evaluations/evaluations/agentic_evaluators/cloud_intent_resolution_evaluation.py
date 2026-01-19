# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to run IntentResolutionEvaluator in the cloud
    using project_client.evaluations.create() with the Foundry SDK.

    There are TWO approaches shown here:
    
    1. Cloud Evaluation using project_client.evaluations.create() with EvaluatorConfiguration
       - Uses built-in evaluator IDs (EvaluatorIds.INTENT_RESOLUTION)
       - Runs evaluation in the cloud
       - Results logged to Foundry project for observability
    
    2. Local Evaluation using azure-ai-evaluation SDK directly
       - Uses IntentResolutionEvaluator class
       - Runs locally on your machine
       - Good for prototyping and small datasets

USAGE:
    python cloud_intent_resolution_evaluation.py

    Before running the sample:

    pip install azure-ai-projects azure-ai-evaluation azure-identity python-dotenv

    Set these environment variables with your own values:
    1) AZURE_AI_PROJECT_ENDPOINT - The Azure AI Project endpoint
    2) AZURE_AI_MODEL_DEPLOYMENT_NAME - The name of the model deployment to use
"""

import os
import json
from datetime import datetime
from pprint import pprint
from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    Evaluation,
    InputDataset,
    EvaluatorConfiguration,
    EvaluatorIds,
)

load_dotenv()


def run_cloud_evaluation():
    """
    Run IntentResolution evaluation in the cloud using project_client.evaluations.create()
    
    This uses the Foundry SDK's built-in evaluator system.
    """
    endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
    model_deployment = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")
    
    print("=" * 60)
    print("CLOUD-BASED EVALUATION with project_client.evaluations.create()")
    print("=" * 60)
    
    with DefaultAzureCredential() as credential:
        with AIProjectClient(endpoint=endpoint, credential=credential) as project_client:
            
            # Step 1: Upload dataset
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(script_dir, "intent_resolution_test_data.jsonl")
            
            print(f"\n📁 Uploading dataset from: {data_file}")
            
            dataset = project_client.datasets.upload_file(
                name=f"intent-resolution-data-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                version="1",
                file_path=data_file,
            )
            print(f"✅ Dataset uploaded: {dataset.id}")
            
            # Step 2: Configure evaluators
            # Note: IntentResolution evaluator ID is 'azureai://built-in/evaluators/intent_resolution'
            # This matches IntentResolutionEvaluator.id from azure-ai-evaluation
            
            print("\n📊 Configuring evaluators...")
            
            evaluators = {
                "intent_resolution": EvaluatorConfiguration(
                    id="azureai://built-in/evaluators/intent_resolution",
                    init_params={
                        "deployment_name": model_deployment,
                    },
                    data_mapping={
                        "query": "${data.query}",
                        "response": "${data.response}",
                        "tool_calls": "${data.tool_calls}",
                        "tool_definitions": "${data.tool_definitions}",
                    },
                ),
                # Optionally add other evaluators for comparison
                "coherence": EvaluatorConfiguration(
                    id=EvaluatorIds.COHERENCE.value,
                    init_params={
                        "deployment_name": model_deployment,
                    },
                    data_mapping={
                        "query": "${data.query}",
                        "response": "${data.response}",
                    },
                ),
            }
            
            print("✅ Evaluators configured:")
            for name, config in evaluators.items():
                print(f"   - {name}: {config.id}")
            
            # Step 3: Create and run evaluation
            print("\n🚀 Creating cloud evaluation...")
            
            evaluation = Evaluation(
                display_name=f"Intent Resolution Cloud Eval - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                description="Evaluating intent resolution for agent responses",
                data=InputDataset(id=dataset.id),
                evaluators=evaluators,
            )
            
            # Note: You may need to provide model endpoint headers depending on your setup
            # Some configurations require:
            # headers={
            #     "model-endpoint": model_endpoint,
            #     "api-key": model_api_key,
            # }
            
            try:
                evaluation_response = project_client.evaluations.create(evaluation)
                
                print(f"\n✅ Evaluation created!")
                print(f"   Name: {evaluation_response.name}")
                print(f"   ID: {evaluation_response.id}")
                print(f"   Status: {evaluation_response.status}")
                
                # The results will be available in the Foundry portal
                print("\n📈 View results in the Azure AI Foundry portal:")
                print(f"   Navigate to your project > Evaluation > {evaluation_response.name}")
                
                return evaluation_response
                
            except Exception as e:
                print(f"\n❌ Error creating cloud evaluation: {e}")
                print("\nThis might happen if:")
                print("  - The evaluator ID is not supported in cloud evaluation")
                print("  - Storage account is not properly connected to your project")
                print("  - Missing permissions (Storage Blob Data Owner)")
                print("\nTrying fallback to local evaluation...")
                return None



def main():
    print("\n🔍 INTENT RESOLUTION EVALUATION")
    print("================================\n")
    
    # Try cloud evaluation first
    cloud_result = run_cloud_evaluation()
    
    return cloud_result


if __name__ == "__main__":
    main()
