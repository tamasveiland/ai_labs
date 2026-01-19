using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TesterConsole
{
    internal static class Config
    {
        public const string ProjectEndpoint = "https://aifksk7hvjr6tbbk.services.ai.azure.com/api/projects/aifksk7hvjr6tbbk-project";
        public const string ModelDeploymentName = "gpt-4o";
        public const string AgentName = "customer-service-agent-live-eval";
        public const string AppInsightsConnection = "InstrumentationKey=0e53dd36-1b2d-4c76-9a73-649f9576289d;IngestionEndpoint=https://swedencentral-0.in.applicationinsights.azure.com/;LiveEndpoint=https://swedencentral.livediagnostics.monitor.azure.com/;ApplicationId=0d40e519-e20c-4ac1-966b-19107a87a753";
    }
}
