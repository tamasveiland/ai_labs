# C# Telemetry Implementation for Fraud Detection Workflow

This is a C# port of the Python telemetry module (`telemetry.py`) for the fraud detection workflow, providing comprehensive observability capabilities.

## Overview

The C# implementation provides the same functionality as the Python version:

- **OpenTelemetry tracing and metrics**: Full distributed tracing support with Activity API
- **Azure Application Insights integration**: Custom events and telemetry
- **Custom business events and metrics**: KPI tracking and business intelligence
- **Cosmos DB operation instrumentation**: Detailed database operation tracking

## Files

- `Telemetry.cs` - Main telemetry implementation with `TelemetryManager` and `CosmosDbInstrumentation` classes
- `FraudDetectionWorkflow.csproj` - Project file with required NuGet packages
- `TelemetryUsageExample.cs` - Comprehensive examples showing how to use the telemetry module
- `README_CSharp_Telemetry.md` - This file

## Required NuGet Packages

```xml
<!-- OpenTelemetry Core -->
<PackageReference Include="OpenTelemetry" Version="1.9.0" />
<PackageReference Include="OpenTelemetry.Exporter.Console" Version="1.9.0" />
<PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol" Version="1.9.0" />
<PackageReference Include="OpenTelemetry.Extensions.Hosting" Version="1.9.0" />

<!-- OpenTelemetry Instrumentation -->
<PackageReference Include="OpenTelemetry.Instrumentation.AspNetCore" Version="1.9.0" />
<PackageReference Include="OpenTelemetry.Instrumentation.Http" Version="1.9.0" />

<!-- Application Insights -->
<PackageReference Include="Microsoft.ApplicationInsights" Version="2.22.0" />
<PackageReference Include="Microsoft.ApplicationInsights.WorkerService" Version="2.22.0" />

<!-- Azure SDK -->
<PackageReference Include="Azure.Identity" Version="1.12.0" />
<PackageReference Include="Microsoft.Azure.Cosmos" Version="3.41.0" />
```

## Environment Variables

Set these environment variables for proper telemetry configuration:

```bash
# Application Insights connection string
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=xxx

# OTLP endpoint for OpenTelemetry (optional)
OTLP_ENDPOINT=http://localhost:4317

# VS Code extension port (optional)
VS_CODE_EXTENSION_PORT=5001
```

## Quick Start

### 1. Initialize Telemetry

```csharp
using FraudDetectionWorkflow.Telemetry;

// Initialize at application startup
GlobalTelemetry.InitializeTelemetry();

// Get telemetry manager instance
var telemetry = GlobalTelemetry.GetTelemetryManager();
```

### 2. Create Workflow Spans

```csharp
var attributes = new Dictionary<string, string>
{
    { "transaction.id", "TXN-12345" },
    { "customer.id", "CUST-67890" }
};

using (var activity = telemetry.CreateWorkflowSpan("fraud_detection_workflow", attributes))
{
    // Your workflow logic here
    Console.WriteLine($"Trace ID: {telemetry.GetCurrentTraceId()}");
}
```

### 3. Send Business Events

```csharp
var properties = new Dictionary<string, string>
{
    { "transaction_id", "TXN-12345" },
    { "risk_score", "0.85" },
    { "decision", "block" }
};

telemetry.SendBusinessEvent("fraud_detection.high_risk_transaction", properties);
```

### 4. Record Metrics

```csharp
// Record transaction processed
telemetry.RecordTransactionProcessed("risk_analysis", "TXN-12345");

// Record risk score
telemetry.RecordRiskScore(0.75, "TXN-12345", "high_risk");

// Record compliance decision
telemetry.RecordComplianceDecision("blocked", "TXN-12345");

// Record fraud alert
telemetry.RecordFraudAlertCreated("ALERT-123", "critical", "block", "TXN-12345");
```

### 5. Cosmos DB Instrumentation

```csharp
var cosmosInstrumentation = new CosmosDbInstrumentation(telemetry);

// Instrument transaction retrieval
var transaction = await cosmosInstrumentation.InstrumentTransactionGetAsync(
    async (transactionId) => 
    {
        // Your Cosmos DB query logic
        return await GetTransactionFromCosmosAsync(transactionId);
    },
    "TXN-12345"
);

// Instrument customer retrieval
var customer = await cosmosInstrumentation.InstrumentCustomerGetAsync(
    async (customerId) => 
    {
        // Your Cosmos DB query logic
        return await GetCustomerFromCosmosAsync(customerId);
    },
    "CUST-67890"
);
```

### 6. Flush Telemetry

```csharp
// Flush before application exit
GlobalTelemetry.FlushTelemetry();
```

## Key Differences from Python Implementation

### 1. Activity API vs Spans
C# uses the native `Activity` API (System.Diagnostics) which is the .NET implementation of OpenTelemetry spans:

```csharp
// Python
with tracer.start_as_current_span("operation") as span:
    span.set_attribute("key", "value")

// C#
using (var activity = tracer.StartActivity("operation"))
{
    activity?.SetTag("key", "value");
}
```

### 2. Async/Await Pattern
C# uses native async/await for asynchronous operations:

```csharp
public async Task<Dictionary<string, object>> InstrumentTransactionGetAsync(
    Func<string, Task<Dictionary<string, object>>> func,
    string transactionId)
{
    // Async implementation
}
```

### 3. Strongly Typed
C# implementation uses strongly typed dictionaries and objects:

```csharp
Dictionary<string, string> attributes
Dictionary<string, object> result
```

### 4. Dependency Injection Ready
The implementation is designed to work with .NET Dependency Injection:

```csharp
services.AddSingleton<TelemetryManager>();
services.AddSingleton<CosmosDbInstrumentation>();
```

## Advanced Features

### Custom Operation Spans

```csharp
// Detailed operation span
using (var activity = telemetry.CreateDetailedOperationSpan(
    "analyze_risk", 
    "risk_analysis",
    new Dictionary<string, string> { { "transaction.id", "TXN-123" } }))
{
    // Operation logic
}

// AI interaction span
using (var activity = telemetry.CreateAiInteractionSpan(
    "gpt-4o",
    "compliance_check",
    new Dictionary<string, string> { { "prompt.tokens", "500" } }))
{
    // AI interaction logic
}

// Data operation span
using (var activity = telemetry.CreateDataOperationSpan(
    "cosmos_db",
    "query",
    new Dictionary<string, string> { { "collection", "Transactions" } }))
{
    // Data operation logic
}
```

### Error Handling

```csharp
using (var activity = telemetry.CreateDetailedOperationSpan("operation", "processing"))
{
    try
    {
        // Risky operation
    }
    catch (Exception ex)
    {
        activity?.SetTag("error", true);
        activity?.SetTag("error.type", ex.GetType().Name);
        activity?.SetTag("error.message", ex.Message);
        
        telemetry.SendBusinessEvent("operation.failed", new Dictionary<string, string>
        {
            { "error_type", ex.GetType().Name },
            { "error_message", ex.Message }
        });
    }
}
```

## Integration with ASP.NET Core

For ASP.NET Core applications, configure in `Program.cs`:

```csharp
var builder = WebApplication.CreateBuilder(args);

// Add OpenTelemetry
builder.Services.AddOpenTelemetry()
    .WithTracing(tracerProviderBuilder =>
    {
        tracerProviderBuilder
            .AddSource("fraud_detection_workflow")
            .AddAspNetCoreInstrumentation()
            .AddHttpClientInstrumentation()
            .AddOtlpExporter();
    })
    .WithMetrics(meterProviderBuilder =>
    {
        meterProviderBuilder
            .AddMeter("fraud_detection_metrics")
            .AddAspNetCoreInstrumentation()
            .AddOtlpExporter();
    });

// Add Application Insights
builder.Services.AddApplicationInsightsTelemetry();

// Register telemetry services
builder.Services.AddSingleton<TelemetryManager>();
builder.Services.AddSingleton<CosmosDbInstrumentation>();

var app = builder.Build();

// Initialize telemetry
var telemetry = app.Services.GetRequiredService<TelemetryManager>();
telemetry.InitializeObservability();
```

## Viewing Telemetry Data

### Azure Application Insights
1. Navigate to your Application Insights resource in Azure Portal
2. View traces in "Transaction search"
3. View custom events in "Events"
4. View metrics in "Metrics explorer"
5. Create custom dashboards and workbooks

### Local Development
- Console output shows trace information
- Use Jaeger or Zipkin for local trace visualization
- OTLP endpoint can be configured to send to local collectors

## Testing

Run the example to verify telemetry is working:

```bash
dotnet run --project FraudDetectionWorkflow.csproj
```

Expected output:
```
🔍 Observability initialized for fraud detection workflow
📊 Application Insights: ✓
🔗 OTLP Endpoint: ✓
🔧 VS Code Extension: ✗
Workflow started with trace ID: 1234567890abcdef
Risk analysis completed
Customer data retrieved
AI compliance check completed
Workflow completed successfully
📊 Business event sent: fraud_detection.high_risk_transaction (multiple channels)
...
```

## Best Practices

1. **Initialize Once**: Call `InitializeObservability()` once at application startup
2. **Use Using Statements**: Always wrap spans in `using` statements for proper disposal
3. **Structured Attributes**: Use meaningful attribute names and structured data
4. **Flush on Exit**: Call `FlushTelemetry()` before application shutdown
5. **Error Recording**: Always record exceptions and errors in spans
6. **Business Events**: Use business events for KPIs and important business logic
7. **Null Checks**: Activities can be null, always use null-conditional operators

## Troubleshooting

### No traces appearing in Application Insights
- Verify `APPLICATIONINSIGHTS_CONNECTION_STRING` is set correctly
- Check network connectivity to Application Insights endpoint
- Wait 2-5 minutes for data to appear (initial ingestion delay)
- Call `FlushTelemetry()` to force immediate send

### Missing metrics
- Ensure meter is initialized before recording metrics
- Verify OTLP endpoint is configured correctly
- Check that metrics are being exported (console exporter for debugging)

### Activities are null
- Verify ActivitySource is created with correct name and version
- Ensure OpenTelemetry SDK is properly configured
- Check that activity listeners are registered

## Resources

- [OpenTelemetry .NET Documentation](https://opentelemetry.io/docs/instrumentation/net/)
- [Azure Application Insights Documentation](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [System.Diagnostics.Activity Documentation](https://docs.microsoft.com/dotnet/api/system.diagnostics.activity)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
