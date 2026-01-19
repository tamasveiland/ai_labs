using System.Text.Json.Serialization;

namespace AzureAIEvaluations.Tests.Models;

/// <summary>
/// Represents a test query for evaluation
/// </summary>
public class TestQuery
{
    [JsonPropertyName("query")]
    public string Query { get; set; } = string.Empty;

    [JsonPropertyName("response")]
    public string Response { get; set; } = string.Empty;

    [JsonPropertyName("context")]
    public string Context { get; set; } = string.Empty;

    [JsonPropertyName("ground_truth")]
    public string GroundTruth { get; set; } = string.Empty;
}

/// <summary>
/// Evaluation result for a single query
/// </summary>
public class EvaluationResult
{
    public string Query { get; set; } = string.Empty;
    public string Response { get; set; } = string.Empty;
    public double GroundednessScore { get; set; }
    public double RelevanceScore { get; set; }
    public double CoherenceScore { get; set; }
    public double FluencyScore { get; set; }
    public double SimilarityScore { get; set; }
    public string? Reasoning { get; set; }
}

/// <summary>
/// Aggregate evaluation metrics
/// </summary>
public class AggregateMetrics
{
    public MetricStatistics Groundedness { get; set; } = new();
    public MetricStatistics Relevance { get; set; } = new();
    public MetricStatistics Coherence { get; set; } = new();
    public MetricStatistics Fluency { get; set; } = new();
    public MetricStatistics Similarity { get; set; } = new();
    public int TotalQueries { get; set; }
}

/// <summary>
/// Statistics for a single metric
/// </summary>
public class MetricStatistics
{
    public double Mean { get; set; }
    public double Min { get; set; }
    public double Max { get; set; }
    public double StdDev { get; set; }
}

/// <summary>
/// Azure AI Evaluator response
/// </summary>
public class EvaluatorResponse
{
    [JsonPropertyName("score")]
    public double Score { get; set; }

    [JsonPropertyName("reasoning")]
    public string? Reasoning { get; set; }
}