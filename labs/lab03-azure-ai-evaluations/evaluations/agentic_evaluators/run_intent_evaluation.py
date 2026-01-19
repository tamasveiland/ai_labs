# ------------------------------------
# Intent Resolution Evaluation using azure-ai-evaluation SDK
# ------------------------------------

"""
USAGE:
    python run_intent_evaluation.py

    Before running:
    pip install azure-ai-evaluation python-dotenv

    Set environment variables:
    - AZURE_OPENAI_ENDPOINT
    - AZURE_AI_MODEL_DEPLOYMENT_NAME (e.g., gpt-4o)
"""

from dotenv import load_dotenv
import os
import json
from pprint import pprint

from azure.ai.evaluation import IntentResolutionEvaluator

load_dotenv()


def main():
    # Configuration
    azure_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    deployment_name = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")
    
    model_config = {
        "azure_endpoint": azure_endpoint,
        "azure_deployment": deployment_name,
        "api_version": "2024-06-01",
    }
    
    # Add API key if available, otherwise uses DefaultAzureCredential
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if api_key:
        model_config["api_key"] = api_key

    # Load test data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(script_dir, "intent_resolution_test_data.jsonl")
    
    print(f"\n📂 Loading: {data_file}")
    test_data = []
    with open(data_file, "r") as f:
        for line in f:
            test_data.append(json.loads(line))
    print(f"✅ Loaded {len(test_data)} test cases\n")

    # Initialize evaluator
    print("🔧 Initializing IntentResolutionEvaluator...")
    evaluator = IntentResolutionEvaluator(model_config=model_config, threshold=3)
    print("✅ Ready\n")

    # Run evaluations
    print("="*60)
    print("EVALUATING")
    print("="*60)

    results = []
    for i, item in enumerate(test_data, 1):
        query = item.get("query", "")
        response = item.get("response", "")
        tool_definitions = item.get("tool_definitions")
        
        print(f"\n[{i}] {query[:60]}...")
        
        try:
            kwargs = {"query": query, "response": response}
            if tool_definitions:
                kwargs["tool_definitions"] = tool_definitions
            
            result = evaluator(**kwargs)
            
            score = result.get("intent_resolution", "N/A")
            passed = result.get("intent_resolution_result", "N/A")
            reason = result.get("intent_resolution_reason", "")[:100]
            
            print(f"    Score: {score}/5 | Result: {passed}")
            print(f"    Reason: {reason}...")
            
            results.append({"case": i, "query": query, **result})
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results.append({"case": i, "query": query, "error": str(e)})

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    scores = [r.get("intent_resolution", 0) for r in results if "intent_resolution" in r]
    passed = sum(1 for r in results if r.get("intent_resolution_result") == "pass")
    
    print(f"Passed: {passed}/{len(results)}")
    if scores:
        print(f"Avg Score: {sum(scores)/len(scores):.2f}/5")

    # Save results
    output_file = os.path.join(script_dir, "intent_eval_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📁 Saved: {output_file}")


if __name__ == "__main__":
    main()
