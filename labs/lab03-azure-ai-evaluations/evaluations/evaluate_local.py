"""
Local Evaluation Script for RAG Application
Demonstrates Azure AI Evaluation SDK with built-in and custom evaluators
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import RAG app
sys.path.append(str(Path(__file__).parent.parent / "src"))

from azure.ai.evaluation import (
    evaluate,
    GroundednessEvaluator,
    RelevanceEvaluator,
    CoherenceEvaluator,
    FluencyEvaluator,
    SimilarityEvaluator,
    AzureOpenAIModelConfiguration
)
from azure.identity import DefaultAzureCredential


def setup_model_config(use_api_key: bool = False) -> AzureOpenAIModelConfiguration:
    """
    Configure Azure OpenAI for prompt-based evaluators.
    
    Args:
        use_api_key: Whether to use API key authentication
        
    Returns:
        AzureOpenAIModelConfiguration instance
    """
    if use_api_key:
        return AzureOpenAIModelConfiguration(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-08-01-preview"
        )
    else:
        # Use managed identity authentication
        return AzureOpenAIModelConfiguration(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-08-01-preview"
        )


def run_evaluation(
    data_path: str = "../data/test_queries.jsonl",
    output_path: str = "./evaluation_results",
    use_api_key: bool = False
):
    """
    Run comprehensive evaluation on RAG application responses.
    
    Args:
        data_path: Path to test dataset (JSONL format)
        output_path: Path to save evaluation results
        use_api_key: Whether to use API key authentication
    """
    print("=" * 80)
    print("Azure AI Evaluations - RAG Application Evaluation")
    print("=" * 80)
    print()
    
    # Configure model for prompt-based evaluators
    print("📋 Configuring Azure OpenAI model...")
    model_config = setup_model_config(use_api_key)
    
    if not use_api_key:
        credential = DefaultAzureCredential()
    else:
        credential = None
    
    # Initialize built-in evaluators
    print("🔧 Initializing evaluators...")
    print("  - Groundedness (Prompt-based)")
    print("  - Relevance (Prompt-based)")
    print("  - Coherence (Prompt-based)")
    print("  - Fluency (Prompt-based)")
    print("  - Similarity (Code-based)")
    print("  - Response Length (Custom Code-based)")
    print()
    
    # RAG-specific evaluators
    if credential:
        groundedness = GroundednessEvaluator(
            model_config=model_config,
            credential=credential
        )
        relevance = RelevanceEvaluator(
            model_config=model_config,
            credential=credential
        )
        coherence = CoherenceEvaluator(
            model_config=model_config,
            credential=credential
        )
        fluency = FluencyEvaluator(
            model_config=model_config,
            credential=credential
        )
    else:
        groundedness = GroundednessEvaluator(model_config=model_config)
        relevance = RelevanceEvaluator(model_config=model_config)
        coherence = CoherenceEvaluator(model_config=model_config)
        fluency = FluencyEvaluator(model_config=model_config)
    
    # Similarity evaluator (code-based, no model needed)
    similarity = SimilarityEvaluator()
    
    # Custom code-based evaluator
    from custom_evaluators.response_metrics import ResponseLengthEvaluator
    response_length = ResponseLengthEvaluator()
    
    # Run evaluation using evaluate() API
    print(f"🚀 Running evaluation on: {data_path}")
    print()
    
    result = evaluate(
        data=data_path,
        evaluators={
            "groundedness": groundedness,
            "relevance": relevance,
            "coherence": coherence,
            "fluency": fluency,
            "similarity": similarity,
            "response_length": response_length
        },
        evaluator_config={
            "groundedness": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}",
                    "context": "${data.context}"
                }
            },
            "relevance": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            },
            "coherence": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            },
            "fluency": {
                "column_mapping": {
                    "response": "${data.response}"
                }
            },
            "similarity": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}",
                    "ground_truth": "${data.ground_truth}"
                }
            },
            "response_length": {
                "column_mapping": {
                    "response": "${data.response}"
                }
            }
        },
        output_path=output_path
    )
    
    # Display results summary
    print()
    print("=" * 80)
    print("📊 Evaluation Results Summary")
    print("=" * 80)
    print()
    
    if "metrics" in result:
        metrics = result["metrics"]
        print(f"{'Metric':<20} {'Mean':<10} {'Std Dev':<10}")
        print("-" * 40)
        for metric_name, values in metrics.items():
            if isinstance(values, dict) and "mean" in values:
                mean = values.get("mean", 0)
                std = values.get("std", 0)
                print(f"{metric_name:<20} {mean:<10.3f} {std:<10.3f}")
    
    print()
    print(f"✅ Evaluation complete! Results saved to: {output_path}")
    print()
    print("📂 Output files:")
    print(f"  - {output_path}/eval_results.jsonl (row-level scores)")
    print(f"  - {output_path}/eval_results.json (aggregate metrics)")
    print()
    
    return result


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_NAME"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Please set these variables or run 'azd env refresh' to load them.")
        sys.exit(1)
    
    # Determine authentication method
    use_api_key = os.getenv("AZURE_OPENAI_API_KEY") is not None
    
    # Run evaluation
    run_evaluation(use_api_key=use_api_key)
