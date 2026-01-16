"""
Script to generate test data for RAG application evaluation
Can be customized to generate data programmatically or prepare existing data
"""
import json
import sys
from pathlib import Path

# Add parent directory to import RAG app
sys.path.append(str(Path(__file__).parent.parent / "src"))


def generate_sample_data(output_path: str = "test_queries.jsonl"):
    """
    Generate sample test queries with ground truth for evaluation.
    In a real scenario, this would come from historical data or SME annotations.
    
    Args:
        output_path: Path to save the generated JSONL file
    """
    print("📝 Generating sample test data...")
    
    # Sample queries with ground truth and context
    # In production, these would come from real user interactions or expert annotations
    test_data = [
        {
            "query": "What is Azure AI Foundry?",
            "ground_truth": "Azure AI Foundry is Microsoft's unified platform for AI application development, previously called Azure AI Studio, offering tools for building, evaluating, and deploying generative AI solutions with enterprise features.",
            "context": "Azure AI Foundry is a comprehensive platform for building AI applications..."
        },
        {
            "query": "How do I implement RAG?",
            "ground_truth": "Implement RAG by combining a retrieval system (like Azure AI Search) with a language model, retrieving relevant documents for a query, and using them as context for response generation.",
            "context": "RAG combines information retrieval with generation..."
        },
        # Add more test cases as needed
    ]
    
    # Save as JSONL
    output_file = Path(__file__).parent.parent / "data" / output_path
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in test_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"✅ Generated {len(test_data)} test cases")
    print(f"💾 Saved to: {output_file}")


def prepare_existing_data(input_path: str, output_path: str = "prepared_queries.jsonl"):
    """
    Prepare existing data for evaluation by formatting it correctly.
    
    Args:
        input_path: Path to input data file (CSV, JSON, etc.)
        output_path: Path to save the formatted JSONL file
    """
    print(f"📂 Preparing data from: {input_path}")
    
    # Example: Read from CSV and convert to JSONL
    # In production, customize this based on your data format
    import pandas as pd
    
    # Read your data
    # df = pd.read_csv(input_path)
    
    # Transform to required format
    # Make sure to include all required columns: query, response, context, ground_truth
    # Avoid timestamp fields as they cause SDK errors
    
    print("✅ Data preparation complete")


def validate_jsonl(file_path: str):
    """
    Validate JSONL file format and required fields.
    
    Args:
        file_path: Path to JSONL file to validate
    """
    print(f"🔍 Validating: {file_path}")
    
    required_fields = {"query", "response", "context", "ground_truth"}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                data = json.loads(line)
                missing_fields = required_fields - set(data.keys())
                
                if missing_fields:
                    print(f"⚠️  Line {i}: Missing fields: {missing_fields}")
                
                # Check for timestamp fields (these cause SDK errors)
                for key, value in data.items():
                    if isinstance(value, str) and 'T' in value and ':' in value:
                        if len(value) > 20:  # Likely a timestamp
                            print(f"⚠️  Line {i}: Field '{key}' appears to contain a timestamp")
                
            except json.JSONDecodeError as e:
                print(f"❌ Line {i}: Invalid JSON - {e}")
                return False
    
    print("✅ Validation complete")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Prepare test data for evaluation")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate sample test data"
    )
    parser.add_argument(
        "--validate",
        type=str,
        help="Validate JSONL file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="test_queries.jsonl",
        help="Output file name"
    )
    
    args = parser.parse_args()
    
    if args.generate:
        generate_sample_data(args.output)
    elif args.validate:
        validate_jsonl(args.validate)
    else:
        print("Usage:")
        print("  python prepare_test_data.py --generate")
        print("  python prepare_test_data.py --validate <file.jsonl>")
