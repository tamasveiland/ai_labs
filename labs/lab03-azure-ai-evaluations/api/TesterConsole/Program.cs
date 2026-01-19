using Azure.AI.Projects;
using Azure.Identity;
using System.Text.Json;

namespace TesterConsole
{
    internal class Program
    {
        static async Task Main(string[] args)
        {
            Console.WriteLine("Running Batch Evaluation with OpenAI Evals API...");
            var credential = new DefaultAzureCredential();
            var projectEndpoint = "https://aifksk7hvjr6tbbk.services.ai.azure.com/api/projects/aifksk7hvjr6tbbk-project";
            var modelDeploymentName = "gpt-4o";
            string agentName = "customer-service-agent-live-eval";

            AIProjectClient client = new(
                endpoint: new Uri(projectEndpoint), 
                tokenProvider: credential);

            // Step 1: Collect responses from the agent
            Console.WriteLine("\n=== Step 1: Collecting Agent Responses ===");
            var testResults = await CollectAgentResponses(client, agentName);

            //// Step 2: Create and run batch evaluation
            Console.WriteLine("\n=== Step 2: Running Batch Evaluation ===");
            await RunBatchEvaluation(client, modelDeploymentName, testResults);

            Console.WriteLine("\nAll done! Press any key to exit...");
            Console.ReadLine();
        }

        private static async Task<List<TestResult>> CollectAgentResponses(AIProjectClient client, string agentName)
        {
            // Create a conversation for testing
            var conversation = client.OpenAI.Conversations.CreateProjectConversation();
            Console.WriteLine($"Created conversation: {conversation.Value.Id}");

            var responsesClient = client.OpenAI.GetProjectResponsesClientForAgent(
                defaultAgent: agentName,
                defaultConversationId: conversation.Value.Id);
            // Load test queries
            List<InputQuery> testQueries = GetTestQueries();
            var testResults = new List<TestResult>();

#pragma warning disable OPENAI001
            foreach (var testQuery in testQueries)
            {
                Console.WriteLine($"\nProcessing query: {testQuery.Query}");
                
                try
                {
                    var response = responsesClient.CreateResponse(testQuery.Query);
                    string responseText = response.Value.GetOutputText();
                    
                    Console.WriteLine($"Response: {responseText.Substring(0, Math.Min(100, responseText.Length))}...");
                    
                    testResults.Add(new TestResult
                    {
                        Query = testQuery.Query,
                        Response = responseText,
                        ToolDefinitions = testQuery.ToolDefinitions,
                        ExpectedToolCalls = testQuery.ToolCalls
                    });
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error: {ex.Message}");
                }
            }
#pragma warning restore OPENAI001

            return testResults;
        }

        private static async Task RunBatchEvaluation(
            AIProjectClient projectClient,
            string modelDeploymentName,
            List<TestResult> testResults)
        {
            // Get OpenAI client for evals
            var openAIClient = projectClient.GetProjectOpenAIClient();

            // Define the data source configuration
            var dataSourceConfig = new
            {
                type = "custom",
                item_schema = new
                {
                    type = "object",
                    properties = new
                    {
                        query = new { type = "string" },
                        response = new { type = "string" },
                        tool_definitions = new
                        {
                            anyOf = new object[]
                            {
                                new { type = "object" },
                                new { type = "array", items = new { type = "object" } }
                            }
                        }
                    },
                    required = new[] { "query", "response" }
                },
                include_sample_schema = true
            };

            // Define testing criteria (evaluators)
            var testingCriteria = new object[]
            {
                new
                {
                    type = "azure_ai_evaluator",
                    name = "intent_resolution",
                    evaluator_name = "builtin.intent_resolution",
                    initialization_parameters = new { deployment_name = modelDeploymentName },
                    data_mapping = new
                    {
                        query = "{{item.query}}",
                        response = "{{item.response}}",
                        tool_definitions = "{{item.tool_definitions}}"
                    }
                },
                new
                {
                    type = "azure_ai_evaluator",
                    name = "task_adherence",
                    evaluator_name = "builtin.task_adherence",
                    initialization_parameters = new { deployment_name = modelDeploymentName },
                    data_mapping = new
                    {
                        query = "{{item.query}}",
                        response = "{{item.response}}",
                        tool_definitions = "{{item.tool_definitions}}"
                    }
                },
                new
                {
                    type = "azure_ai_evaluator",
                    name = "relevance",
                    evaluator_name = "builtin.relevance",
                    initialization_parameters = new { deployment_name = modelDeploymentName },
                    data_mapping = new
                    {
                        query = "{{item.query}}",
                        response = "{{item.response}}"
                    }
                }
            };

            Console.WriteLine("\nCreating evaluation...");

            // Serialize the configuration
            var dataSourceConfigJson = JsonSerializer.Serialize(dataSourceConfig);
            var testingCriteriaJson = JsonSerializer.Serialize(testingCriteria);

            Console.WriteLine($"Data Source Config: {dataSourceConfigJson}");
            Console.WriteLine($"Testing Criteria: {testingCriteriaJson}");

            // Note: The actual eval creation would use the OpenAI Evals API
            // For now, we'll save the data for evaluation
            await SaveEvaluationData(testResults);

            Console.WriteLine("\n✓ Evaluation data prepared");
            Console.WriteLine("To complete the evaluation:");
            Console.WriteLine("1. The data has been saved to 'evaluation_data.jsonl'");
            Console.WriteLine("2. You can use the Azure AI Foundry portal to run evaluations");
            Console.WriteLine("3. Or use the Python SDK which has better support for the Evals API");
        }

        private static async Task SaveEvaluationData(List<TestResult> testResults)
        {
            var outputPath = "evaluation_data.jsonl";
            using var writer = new StreamWriter(outputPath);
            
            foreach (var result in testResults)
            {
                var item = new
                {
                    query = result.Query,
                    response = result.Response,
                    tool_definitions = result.ToolDefinitions
                };
                
                var json = JsonSerializer.Serialize(item);
                await writer.WriteLineAsync(json);
            }
            
            Console.WriteLine($"\n✓ Saved {testResults.Count} items to {outputPath}");
        }

        private static List<InputQuery> GetTestQueries()
        {
            var lines = File.ReadAllLines("test_queries.jsonl");
            var testQueries = lines
                .Where(line => !string.IsNullOrWhiteSpace(line))
                .Select(line => JsonSerializer.Deserialize<InputQuery>(line, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                }))
                .Where(q => q != null)
                .ToList();

            return testQueries!;
        }
    }

    // Helper class to store test results
    public class TestResult
    {
        public string Query { get; set; } = string.Empty;
        public string Response { get; set; } = string.Empty;
        public List<ToolDefinition>? ToolDefinitions { get; set; }
        public List<ToolCall>? ExpectedToolCalls { get; set; }
    }
}
