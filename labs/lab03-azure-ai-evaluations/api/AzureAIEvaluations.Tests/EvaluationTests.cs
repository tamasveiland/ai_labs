using AzureAIEvaluations.Tests.Models;
using AzureAIEvaluations.Tests.Services;
using FluentAssertions;
using Microsoft.Extensions.Configuration;
using System.Text.Json;
using Xunit.Abstractions;

namespace AzureAIEvaluations.Tests;

/// <summary>
/// Azure AI Evaluation Tests
/// </summary>
public class EvaluationTests
{
    private readonly ITestOutputHelper _output;
    private readonly AzureAIEvaluationService _evaluationService;
    private readonly IConfiguration _configuration;

    public EvaluationTests(ITestOutputHelper output)
    {
        _output = output;
        
        // Build configuration
        _configuration = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json", optional: true)
            .AddEnvironmentVariables()
            .Build();

        _evaluationService = new AzureAIEvaluationService(_configuration);
    }

    [Fact]
    public async Task SingleQuery_Evaluation_ShouldPassQualityThresholds()
    {
        // Arrange
        var testQuery = new TestQuery
        {
            Query = "What is Azure AI Foundry?",
            Response = "Azure AI Foundry is Microsoft's unified platform for AI application development, offering tools for building, evaluating, and deploying generative AI solutions with enterprise features.",
            Context = "Azure AI Foundry (previously Azure AI Studio) is a comprehensive development platform that provides teams with tools to build, test, and deploy AI applications. It offers integrated features for prompt engineering, model fine-tuning, evaluation frameworks, and responsible AI practices.",
            GroundTruth = "Azure AI Foundry is Microsoft's unified platform for AI application development, previously called Azure AI Studio, offering tools for building, evaluating, and deploying generative AI solutions with enterprise features."
        };

        // Act
        var result = await _evaluationService.EvaluateQueryAsync(testQuery);

        // Assert
        _output.WriteLine($"Query: {result.Query}");
        _output.WriteLine($"Groundedness: {result.GroundednessScore:F2}");
        _output.WriteLine($"Relevance: {result.RelevanceScore:F2}");
        _output.WriteLine($"Coherence: {result.CoherenceScore:F2}");
        _output.WriteLine($"Fluency: {result.FluencyScore:F2}");
        _output.WriteLine($"Similarity: {result.SimilarityScore:F2}");
        _output.WriteLine($"Reasoning: {result.Reasoning}");

        // Quality thresholds
        result.GroundednessScore.Should().BeGreaterOrEqualTo(3.0, "Response should be grounded in context");
        result.RelevanceScore.Should().BeGreaterOrEqualTo(3.0, "Response should be relevant");
        result.CoherenceScore.Should().BeGreaterOrEqualTo(3.5, "Response should be coherent");
        result.FluencyScore.Should().BeGreaterOrEqualTo(4.0, "Response should be fluent");
    }

    [Fact]
    public async Task MultipleQueries_BatchEvaluation_ShouldCalculateAggregateMetrics()
    {
        // Arrange
        var testQueries = LoadTestQueries("testdata/test_queries.jsonl");
        testQueries.Should().NotBeEmpty("Test data file should contain queries");

        // Act
        var results = new List<EvaluationResult>();
        foreach (var query in testQueries.Take(5)) // Limit for test execution time
        {
            var result = await _evaluationService.EvaluateQueryAsync(query);
            results.Add(result);
            
            _output.WriteLine($"\nQuery: {query.Query}");
            _output.WriteLine($"  Groundedness: {result.GroundednessScore:F2}");
            _output.WriteLine($"  Relevance: {result.RelevanceScore:F2}");
            _output.WriteLine($"  Coherence: {result.CoherenceScore:F2}");
            _output.WriteLine($"  Fluency: {result.FluencyScore:F2}");
            _output.WriteLine($"  Similarity: {result.SimilarityScore:F2}");
        }

        var aggregateMetrics = _evaluationService.CalculateAggregateMetrics(results);

        // Assert
        _output.WriteLine("\n=== Aggregate Metrics ===");
        _output.WriteLine($"Total Queries: {aggregateMetrics.TotalQueries}");
        _output.WriteLine($"Groundedness - Mean: {aggregateMetrics.Groundedness.Mean:F2}, StdDev: {aggregateMetrics.Groundedness.StdDev:F2}");
        _output.WriteLine($"Relevance    - Mean: {aggregateMetrics.Relevance.Mean:F2}, StdDev: {aggregateMetrics.Relevance.StdDev:F2}");
        _output.WriteLine($"Coherence    - Mean: {aggregateMetrics.Coherence.Mean:F2}, StdDev: {aggregateMetrics.Coherence.StdDev:F2}");
        _output.WriteLine($"Fluency      - Mean: {aggregateMetrics.Fluency.Mean:F2}, StdDev: {aggregateMetrics.Fluency.StdDev:F2}");
        _output.WriteLine($"Similarity   - Mean: {aggregateMetrics.Similarity.Mean:F2}, StdDev: {aggregateMetrics.Similarity.StdDev:F2}");

        aggregateMetrics.Groundedness.Mean.Should().BeGreaterOrEqualTo(3.0);
        aggregateMetrics.Relevance.Mean.Should().BeGreaterOrEqualTo(3.0);
        aggregateMetrics.Coherence.Mean.Should().BeGreaterOrEqualTo(3.5);
        aggregateMetrics.Fluency.Mean.Should().BeGreaterOrEqualTo(4.0);
    }

    [Theory]
    [InlineData("What is RAG?", "RAG combines retrieval with generation.", "Retrieval-Augmented Generation", 3.0)]
    [InlineData("Explain AI", "AI enables machines to learn.", "Artificial Intelligence basics", 3.0)]
    public async Task ParameterizedEvaluation_ShouldMeetMinimumRelevance(
        string query, 
        string response, 
        string context,
        double minimumRelevance)
    {
        // Arrange & Act
        var result = await _evaluationService.EvaluateRelevanceAsync(query, response);

        // Assert
        _output.WriteLine($"Query: {query}");
        _output.WriteLine($"Response: {response}");
        _output.WriteLine($"Relevance Score: {result.Score:F2}");
        _output.WriteLine($"Reasoning: {result.Reasoning}");

        result.Score.Should().BeGreaterOrEqualTo(minimumRelevance);
    }

    private List<TestQuery> LoadTestQueries(string filePath)
    {
        var queries = new List<TestQuery>();

        if (!File.Exists(filePath))
        {
            _output.WriteLine($"Warning: Test data file not found: {filePath}");
            return queries;
        }

        foreach (var line in File.ReadAllLines(filePath))
        {
            if (string.IsNullOrWhiteSpace(line)) continue;

            try
            {
                var query = JsonSerializer.Deserialize<TestQuery>(line);
                if (query != null)
                {
                    queries.Add(query);
                }
            }
            catch (JsonException ex)
            {
                _output.WriteLine($"Error parsing line: {ex.Message}");
            }
        }

        return queries;
    }
}