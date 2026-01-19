using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace TesterConsole
{

    public static class FoundryEvaluationPolling
    {
        public static async Task<EvaluationRun> GetEvaluationRunAsync(
            HttpClient http,
            string projectEndpoint,
            string evaluationIdOrName,
            CancellationToken ct = default)
        {
            var url = $"{projectEndpoint.TrimEnd('/')}/evaluations/runs/{evaluationIdOrName}?api-version=2025-05-15-preview";

            string token = await Foundry.GetFoundryAccessTokenAsync();
            using var req = new HttpRequestMessage(HttpMethod.Get, url);
            req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

            using var resp = await http.SendAsync(req, ct);
            resp.EnsureSuccessStatusCode();

            var json = await resp.Content.ReadAsStringAsync(ct);
            return JsonSerializer.Deserialize<EvaluationRun>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            })!;
        }

        public static async Task<EvaluationRun> PollUntilCompleteAsync(
            HttpClient http,
            string projectEndpoint,
            string evaluationIdOrName,
            TimeSpan pollInterval,
            CancellationToken ct = default)
        {
            while (true)
            {
                var run = await GetEvaluationRunAsync(http, projectEndpoint, evaluationIdOrName, ct);

                // The Agent Evaluation response defines status values such as Running/Completed/Failed.
                if (string.Equals(run.status, "Completed", StringComparison.OrdinalIgnoreCase) ||
                    string.Equals(run.status, "Failed", StringComparison.OrdinalIgnoreCase))
                {
                    return run;
                }

                await Task.Delay(pollInterval, ct);
            }
        }
    }

    // Generic Evaluation "Get" returns an Evaluation object; keep only what you need.
    public sealed record EvaluationRun(
        string id,
        string status,
        Dictionary<string, object>? evaluators = null,
        Dictionary<string, object>? properties = null,
        Dictionary<string, string>? tags = null
    );

}
