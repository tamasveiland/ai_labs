using Azure.Core;
using Azure.Identity;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace TesterConsole
{

    public sealed class FoundryAgentEvaluationRestClient
    {
        private readonly HttpClient _http;

        public FoundryAgentEvaluationRestClient(HttpClient http) => _http = http;

        /// <param name="projectEndpoint">
        /// e.g. https://<account>.services.ai.azure.com/api/projects/<project>
        /// (or .../api/projects/_project for default project)
        /// </param>
        public async Task<StartEvalResponse> StartAgentEvaluationAsync(
            string projectEndpoint,
            string runId,
            string threadId,
            string appInsightsConnectionString,
            IDictionary<string, EvaluatorConfiguration> evaluators,
            CancellationToken ct = default)
        {
            // POST {endpoint}/evaluations/runs:runAgent?api-version=2025-05-15-preview
            var url = $"{projectEndpoint.TrimEnd('/')}/evaluations/runs:runAgent?api-version=2025-05-15-preview";

            var payload = new
            {
                runId,
                threadId, // currently mandatory per REST docs
                evaluators, // required
                appInsightsConnectionString, // required (results + error logs)
                redactionConfiguration = new { redactScoreProperties = true },
                samplingConfiguration = new { name = "default", samplingPercent = 100, maxRequestRate = 1000 }
            };

            string token = await Foundry.GetFoundryAccessTokenAsync();
            using var req = new HttpRequestMessage(HttpMethod.Post, url);
            req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            req.Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

            using HttpResponseMessage resp = await _http.SendAsync(req, ct);
            resp.EnsureSuccessStatusCode();

            var json = await resp.Content.ReadAsStringAsync(ct);
            return JsonSerializer.Deserialize<StartEvalResponse>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            })!;
        }

    }




    public sealed record EvaluatorConfiguration(
        string id,
        IDictionary<string, object>? initParams = null,
        IDictionary<string, object>? dataMapping = null
    );

    // Minimal shape from the Create Agent Evaluation response: { id, status, error?, result?[] }
    public sealed record StartEvalResponse(
        string id,
        string status,
        string? error = null
    );

}
