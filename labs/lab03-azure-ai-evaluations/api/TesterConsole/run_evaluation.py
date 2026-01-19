"""
Run batch evaluation using the Azure AI Projects OpenAI Evals API.
This script reads the evaluation_data.jsonl file created by the C# program
and runs evaluations using the same approach as sample_intent_resolution.py.

Requirements:
    pip install "azure-ai-projects>=2.0.0b1" azure-identity python-dotenv
"""

import os
import json
import time
from dotenv import load_dotenv
from pprint import pprint

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam,
    SourceFileContent,
    SourceFileContentContent,
)
from openai.types.eval_create_params import DataSourceConfigCustom

load_dotenv()


def main():
    # Configuration from environment
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    model_deployment_name = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", 
                            os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"))
    
    print("="*60)
    print("BATCH EVALUATION WITH AZURE AI PROJECTS EVALS API")
    print("="*60 + "\n")
    
    if not endpoint:
        print("❌ Error: AZURE_AI_PROJECT_ENDPOINT environment variable not set")
        print("Please set this variable in your .env file or environment")
        return 1
    
    print(f"Using AI Project Endpoint: {endpoint}")
    print(f"Using Model Deployment: {model_deployment_name}\n")
    
    # Load the data created by C#
    data_file = "./bin/Debug/net9.0/evaluation_data.jsonl"
    
    if not os.path.exists(data_file):
        print(f"❌ Error: {data_file} not found")
        print("Please run the C# program first to generate the data")
        return 1
    
    print(f"📂 Loading data from: {data_file}")
    
    test_data = []
    with open(data_file, 'r') as f:
        for line in f:
            test_data.append(json.loads(line))
    
    print(f"✅ Loaded {len(test_data)} test items\n")
    
    # Create AI Project client (same approach as sample_intent_resolution.py)
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential, api_version="2024-08-06") as project_client,
        project_client.get_openai_client() as client,
    ):
        print("✓ Connected to AI Project\n")
        
        # Define data source configuration (matching sample_intent_resolution.py)
        data_source_config = DataSourceConfigCustom(
            {
                "type": "custom",
                "item_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "object"}}]},
                        "response": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "object"}}]},
                        "tool_definitions": {
                            "anyOf": [{"type": "object"}, {"type": "array", "items": {"type": "object"}}]
                        },
                    },
                    "required": ["query", "response"],
                },
                "include_sample_schema": True,
            }
        )
        
        # Define testing criteria (matching sample_intent_resolution.py)
        testing_criteria = [
            {
                "type": "azure_ai_evaluator",
                "name": "intent_resolution",
                "evaluator_name": "builtin.intent_resolution",
                "initialization_parameters": {"deployment_name": f"{model_deployment_name}"},
                "data_mapping": {
                    "query": "{{item.query}}",
                    "response": "{{item.response}}",
                    "tool_definitions": "{{item.tool_definitions}}",
                },
                "threshold": {
                    "metric": "intent_resolution",
                    "min": 4.0,
                    "aggregate": "mean"
                }
            }
        ]
        
        print("Creating Evaluation...")
        eval_object = client.evals.create(
            name="Agent Batch Evaluation - Intent Resolution (from C# data)",
            data_source_config=data_source_config,
            testing_criteria=testing_criteria,  # type: ignore
        )
        print(f"✓ Evaluation created: {eval_object.id}\n")
        
        print("Get Evaluation by Id...")
        eval_object_response = client.evals.retrieve(eval_object.id)
        print("Eval Response:")
        pprint(eval_object_response)
        print()
        
        # Convert test data to SourceFileContentContent items
        print("Creating Eval Run with loaded data...")
        content_items = []
        for item in test_data:
            content_item = {
                "query": item["query"],
                "response": item["response"]
            }
            # Include tool_definitions if present
            if "tool_definitions" in item and item["tool_definitions"]:
                content_item["tool_definitions"] = item["tool_definitions"]
            content_items.append(SourceFileContentContent(item=content_item))
        
        eval_run_object = client.evals.runs.create(
            eval_id=eval_object.id,
            name="batch_run_from_csharp",
            metadata={"source": "csharp_agent", "scenario": "customer_service"},
            data_source=CreateEvalJSONLRunDataSourceParam(
                type="jsonl",
                source=SourceFileContent(
                    type="file_content",
                    content=content_items,
                ),
            ),
        )
        
        print(f"✓ Eval Run created: {eval_run_object.id}")
        pprint(eval_run_object)
        print()
        
        print("Waiting for evaluation to complete...")
        print("(This may take a few minutes)\n")
        
        while True:
            run = client.evals.runs.retrieve(run_id=eval_run_object.id, eval_id=eval_object.id)
            print(f"Status: {run.status}")
            
            if run.status == "completed" or run.status == "failed":
                print("\n" + "="*60)
                if run.status == "completed":
                    print("✓ EVALUATION COMPLETED")
                else:
                    print("❌ EVALUATION FAILED")
                print("="*60 + "\n")
                
                # Get output items
                output_items = list(client.evals.runs.output_items.list(run_id=run.id, eval_id=eval_object.id))
                
                print(f"📊 Results for {len(output_items)} items:\n")
                for idx, item in enumerate(output_items, 1):
                    print(f"Item {idx}:")
                    pprint(item)
                    print()
                
                if run.report_url:
                    print(f"📊 View detailed report: {run.report_url}")
                
                break
            
            time.sleep(5)
        
        print("\n✓ Evaluation complete!")
        return 0


if __name__ == "__main__":
    exit(main() or 0)