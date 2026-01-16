"""
Analyze evaluation results and generate summary reports
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any


def load_evaluation_results(results_dir: str = "../evaluations/evaluation_results") -> Dict[str, Any]:
    """
    Load evaluation results from JSON file.
    
    Args:
        results_dir: Directory containing evaluation results
        
    Returns:
        Dictionary with evaluation results
    """
    results_path = Path(__file__).parent.parent / "evaluations" / "evaluation_results"
    
    # Try different possible result file names
    possible_files = [
        results_path / "eval_results.json",
        results_path / "results.json",
        results_path / "evaluation_results.json"
    ]
    
    for file_path in possible_files:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
    
    raise FileNotFoundError(f"No results file found in {results_path}")


def create_summary_table(metrics: Dict[str, Dict[str, float]]) -> str:
    """
    Create a formatted markdown table of metrics.
    
    Args:
        metrics: Dictionary of metric names to their statistics
        
    Returns:
        Markdown formatted table
    """
    table = "| Metric | Mean | Std Dev | Min | Max |\n"
    table += "|--------|------|---------|-----|-----|\n"
    
    for metric_name, values in sorted(metrics.items()):
        if isinstance(values, dict):
            mean = values.get("mean", 0)
            std = values.get("std", 0)
            min_val = values.get("min", 0)
            max_val = values.get("max", 0)
            
            table += f"| {metric_name} | {mean:.3f} | {std:.3f} | {min_val:.3f} | {max_val:.3f} |\n"
    
    return table


def determine_status(score: float, metric_name: str) -> str:
    """
    Determine if a metric meets quality thresholds.
    
    Args:
        score: Metric score
        metric_name: Name of the metric
        
    Returns:
        Status emoji (✅, ⚠️, ❌)
    """
    # Define thresholds for different metrics
    thresholds = {
        "groundedness": {"good": 4.0, "acceptable": 3.0},
        "relevance": {"good": 4.0, "acceptable": 3.0},
        "coherence": {"good": 4.0, "acceptable": 3.0},
        "fluency": {"good": 4.0, "acceptable": 3.0},
        "similarity": {"good": 3.5, "acceptable": 2.5},
    }
    
    # Get threshold for this metric, default to medium thresholds
    threshold = thresholds.get(
        metric_name.lower(),
        {"good": 4.0, "acceptable": 3.0}
    )
    
    if score >= threshold["good"]:
        return "✅"
    elif score >= threshold["acceptable"]:
        return "⚠️"
    else:
        return "❌"


def create_markdown_summary(results: Dict[str, Any]) -> str:
    """
    Create a comprehensive markdown summary of evaluation results.
    
    Args:
        results: Evaluation results dictionary
        
    Returns:
        Markdown formatted summary
    """
    summary = "# 🎯 Evaluation Results Summary\n\n"
    
    # Add metadata
    if "row_count" in results:
        summary += f"**Total Queries Evaluated**: {results['row_count']}\n\n"
    
    # Add metrics table
    if "metrics" in results:
        summary += "## 📊 Metrics Overview\n\n"
        summary += create_summary_table(results["metrics"])
        summary += "\n"
        
        # Add status indicators
        summary += "## 🎭 Quality Assessment\n\n"
        summary += "| Metric | Score | Status |\n"
        summary += "|--------|-------|--------|\n"
        
        for metric_name, values in sorted(results["metrics"].items()):
            if isinstance(values, dict) and "mean" in values:
                mean = values["mean"]
                status = determine_status(mean, metric_name)
                summary += f"| {metric_name} | {mean:.3f} | {status} |\n"
        
        summary += "\n"
        summary += "**Legend**: ✅ Excellent (≥4.0) | ⚠️ Acceptable (≥3.0) | ❌ Needs Improvement (<3.0)\n"
    
    return summary


def save_summary(summary: str, output_path: str = "evaluation_summary.md"):
    """
    Save markdown summary to file.
    
    Args:
        summary: Markdown summary text
        output_path: Path to save the summary
    """
    output_file = Path(__file__).parent / output_path
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"📄 Summary saved to: {output_file}")


def print_summary(results: Dict[str, Any]):
    """
    Print evaluation summary to console.
    
    Args:
        results: Evaluation results dictionary
    """
    print()
    print("=" * 80)
    print("📊 EVALUATION RESULTS ANALYSIS")
    print("=" * 80)
    print()
    
    if "row_count" in results:
        print(f"Total Queries Evaluated: {results['row_count']}")
        print()
    
    if "metrics" in results:
        print(f"{'Metric':<25} {'Mean':<10} {'Status':<10}")
        print("-" * 50)
        
        for metric_name, values in sorted(results["metrics"].items()):
            if isinstance(values, dict) and "mean" in values:
                mean = values["mean"]
                status = determine_status(mean, metric_name)
                print(f"{metric_name:<25} {mean:<10.3f} {status:<10}")
    
    print()


if __name__ == "__main__":
    try:
        # Load results
        results = load_evaluation_results()
        
        # Print to console
        print_summary(results)
        
        # Create and save markdown summary
        markdown_summary = create_markdown_summary(results)
        save_summary(markdown_summary)
        
        print("✅ Analysis complete!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print()
        print("Please run the evaluation first:")
        print("  cd evaluations")
        print("  python evaluate_local.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
