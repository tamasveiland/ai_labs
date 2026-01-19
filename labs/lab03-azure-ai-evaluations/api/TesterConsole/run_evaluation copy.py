"""
Run batch evaluation using the Azure AI Evaluation SDK.
This script reads the evaluation_data.jsonl file created by the C# program
and runs evaluations using the Azure AI Evaluation SDK with built-in evaluators.

Requirements:
    pip install azure-ai-evaluation azure-identity python-dotenv
"""

import os
import json
from dotenv import load_dotenv
from pprint import pprint

from azure.identity import DefaultAzureCredential
from azure.ai.evaluation import (
    evaluate,
    IntentResolutionEvaluator,
    RelevanceEvaluator,
    AzureOpenAIModelConfiguration,
)

load_dotenv()


def main():
    # Configuration from environment
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    model_deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    
    # Optional: Azure AI Project info for cloud logging
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    resource_group = os.environ.get("AZURE_RESOURCE_GROUP")
    project_name = os.environ.get("AZURE_AI_PROJECT_NAME")
    
    print("="*60)
    print("BATCH EVALUATION WITH AZURE AI EVALUATION SDK")
    print("="*60 + "\n")
    
    if not azure_endpoint:
        print("❌ Error: AZURE_OPENAI_ENDPOINT environment variable not set")
        print("Please set this variable in your .env file or environment")
        return 1
    
    print(f"Using Azure OpenAI Endpoint: {azure_endpoint}")
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
    
    # Setup Azure OpenAI model configuration
    credential = DefaultAzureCredential()
    
    model_config = AzureOpenAIModelConfiguration(
        azure_deployment=model_deployment_name,
        azure_endpoint=azure_endpoint,
        api_version="2024-08-01-preview"
    )
    
    print("🔧 Initializing evaluators...")
    print("  - Intent Resolution (Agentic evaluator)")
    print("  - Relevance (Quality evaluator)")
    print()
    
    # Initialize evaluators
    intent_resolution = IntentResolutionEvaluator(
        model_config=model_config,
        credential=credential,
        threshold=3  # Minimum acceptable score (1-5 scale)
    )
    
    relevance = RelevanceEvaluator(
        model_config=model_config,
        credential=credential
    )
    
    # Configure Azure AI Project for cloud logging (optional)
    azure_ai_project = None
    if all([subscription_id, resource_group, project_name]):
        azure_ai_project = {
            "subscription_id": subscription_id,
            "resource_group_name": resource_group,
            "project_name": project_name
        }
        print(f"☁️  Logging results to Azure AI Foundry project: {project_name}")
    else:
        print("ℹ️  Running local-only evaluation (results won't appear in Foundry)")
        print("   To enable cloud logging, set: AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AZURE_AI_PROJECT_NAME")
    print()
    
    # Run evaluation
    print("🚀 Running evaluation...")
    print("(This may take a few minutes)\n")
    
    result = evaluate(
        data=data_file, #test_data,
        evaluators={
            "intent_resolution": intent_resolution,
            "relevance": relevance,
        },
        evaluator_config={
            "intent_resolution": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}",
                }
            },
            "relevance": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            }
        },
        azure_ai_project=azure_ai_project,
        evaluation_name="Agent Batch Evaluation from C#"
    )
    
    # Display results summary
    print("\n" + "="*60)
    print("✓ EVALUATION COMPLETED")
    print("="*60 + "\n")
    
    print("📊 Evaluation Results Summary\n")
    
    # Print aggregate metrics
    if hasattr(result, 'metrics') and result.metrics:
        print(f"{'Metric':<35} {'Value':<15}")
        print("-" * 50)
        for metric_name, value in result.metrics.items():
            if isinstance(value, float):
                print(f"{metric_name:<35} {value:<15.3f}")
            else:
                print(f"{metric_name:<35} {str(value):<15}")
        print()
    
    # Print row-level results
    if hasattr(result, 'rows') and result.rows:
        print(f"\nDetailed Results ({len(result.rows)} items):\n")
        for idx, row in enumerate(result.rows, 1):
            print(f"Item {idx}:")
            pprint(row)
            print()
    
    print("\n✓ Evaluation complete!")
    
    if azure_ai_project:
        print(f"\n📊 View results in Azure AI Foundry: https://ai.azure.com")
    
    return 0


if __name__ == "__main__":
    exit(main() or 0)