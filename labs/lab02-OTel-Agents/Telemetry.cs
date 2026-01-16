using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.ApplicationInsights;
using Microsoft.ApplicationInsights.DataContracts;
using Microsoft.ApplicationInsights.Extensibility;
using OpenTelemetry;
using OpenTelemetry.Exporter;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

namespace FraudDetectionWorkflow.Telemetry
{
    /// <summary>
    /// Telemetry and Observability Module for Fraud Detection Workflow
    /// 
    /// This module provides comprehensive observability capabilities including:
    /// - OpenTelemetry tracing and metrics
    /// - Azure Application Insights integration
    /// - Custom business events and metrics
    /// - Cosmos DB operation instrumentation
    /// </summary>
    public class TelemetryManager
    {
        private ActivitySource _tracer;
        private Meter _meter;
        private TelemetryClient _telemetryClient;
        private bool _initialized = false;
        
        // Metrics
        private Counter<long> _transactionCounter;
        private Histogram<double> _riskScoreHistogram;
        private Counter<long> _complianceDecisionCounter;
        
        private const string ServiceName = "fraud_detection_workflow";
        private const string ServiceVersion = "1.0.0";
        
        public TelemetryManager()
        {
        }
        
        /// <summary>
        /// Initialize observability with Azure Application Insights and local tracing.
        /// </summary>
        public void InitializeObservability()
        {
            if (_initialized)
                return;
            
            // Get configuration from environment variables
            var appInsightsConnectionString = Environment.GetEnvironmentVariable("APPLICATIONINSIGHTS_CONNECTION_STRING");
            var otlpEndpoint = Environment.GetEnvironmentVariable("OTLP_ENDPOINT");
            var vsCodeExtensionPort = Environment.GetEnvironmentVariable("VS_CODE_EXTENSION_PORT");
            
            // Initialize ActivitySource for tracing
            _tracer = new ActivitySource(ServiceName, ServiceVersion);
            
            // Initialize Meter for metrics
            _meter = new Meter("fraud_detection_metrics", ServiceVersion);
            
            // Setup OpenTelemetry tracing
            var tracerProviderBuilder = Sdk.CreateTracerProviderBuilder()
                .SetResourceBuilder(ResourceBuilder.CreateDefault()
                    .AddService(ServiceName, serviceVersion: ServiceVersion))
                .AddSource(ServiceName);
            
            // Add OTLP exporter if endpoint is configured
            if (!string.IsNullOrEmpty(otlpEndpoint))
            {
                tracerProviderBuilder.AddOtlpExporter(options =>
                {
                    options.Endpoint = new Uri(otlpEndpoint);
                    options.Protocol = OtlpExportProtocol.Grpc;
                });
            }
            
            // Add console exporter for local debugging
            tracerProviderBuilder.AddConsoleExporter();
            
            // Build the tracer provider
            var tracerProvider = tracerProviderBuilder.Build();
            
            // Setup OpenTelemetry metrics
            var meterProviderBuilder = Sdk.CreateMeterProviderBuilder()
                .SetResourceBuilder(ResourceBuilder.CreateDefault()
                    .AddService(ServiceName, serviceVersion: ServiceVersion))
                .AddMeter("fraud_detection_metrics");
            
            // Add OTLP exporter for metrics if endpoint is configured
            if (!string.IsNullOrEmpty(otlpEndpoint))
            {
                meterProviderBuilder.AddOtlpExporter(options =>
                {
                    options.Endpoint = new Uri(otlpEndpoint);
                    options.Protocol = OtlpExportProtocol.Grpc;
                });
            }
            
            // Add console exporter for local debugging
            meterProviderBuilder.AddConsoleExporter();
            
            var meterProvider = meterProviderBuilder.Build();
            
            // Initialize Application Insights client
            if (!string.IsNullOrEmpty(appInsightsConnectionString))
            {
                var config = TelemetryConfiguration.CreateDefault();
                config.ConnectionString = appInsightsConnectionString;
                _telemetryClient = new TelemetryClient(config);
                _telemetryClient.Context.Component.Version = ServiceVersion;
                _telemetryClient.Context.Device.Id = ServiceName;
            }
            
            // Initialize custom metrics
            InitializeMetrics();
            
            Console.WriteLine("🔍 Observability initialized for fraud detection workflow");
            Console.WriteLine($"📊 Application Insights: {(!string.IsNullOrEmpty(appInsightsConnectionString) ? "✓" : "✗")}");
            Console.WriteLine($"🔗 OTLP Endpoint: {(!string.IsNullOrEmpty(otlpEndpoint) ? "✓" : "✗")}");
            Console.WriteLine($"🔧 VS Code Extension: {(!string.IsNullOrEmpty(vsCodeExtensionPort) ? "✓" : "✗")}");
            
            _initialized = true;
        }
        
        /// <summary>
        /// Initialize custom metrics for business KPIs.
        /// </summary>
        private void InitializeMetrics()
        {
            _transactionCounter = _meter.CreateCounter<long>(
                "fraud_detection.transactions.processed",
                unit: "1",
                description: "Number of transactions processed");
            
            _riskScoreHistogram = _meter.CreateHistogram<double>(
                "fraud_detection.risk_score.distribution",
                unit: "1",
                description: "Distribution of risk scores");
            
            _complianceDecisionCounter = _meter.CreateCounter<long>(
                "fraud_detection.compliance.decisions",
                unit: "1",
                description: "Number of compliance decisions by type");
        }
        
        /// <summary>
        /// Flush telemetry to ensure events are sent immediately.
        /// </summary>
        public void FlushTelemetry()
        {
            if (_telemetryClient != null)
            {
                _telemetryClient.Flush();
                // Wait a moment for flushing to complete
                Task.Delay(1000).Wait();
                Console.WriteLine("📊 Telemetry flushed to Application Insights");
            }
        }
        
        /// <summary>
        /// Send business event using multiple OpenTelemetry approaches for comprehensive tracing.
        /// </summary>
        public void SendBusinessEvent(string eventName, Dictionary<string, string> properties)
        {
            // Method 1: OpenTelemetry Event (guaranteed to appear in traces)
            var currentActivity = Activity.Current;
            if (currentActivity != null)
            {
                var activityEvent = new ActivityEvent($"business_event.{eventName}");
                foreach (var prop in properties)
                {
                    activityEvent.Tags.Add(new KeyValuePair<string, object?>(prop.Key, prop.Value));
                }
                currentActivity.AddEvent(activityEvent);
            }
            
            // Method 2: OpenTelemetry Custom Span (appears as separate trace)
            using (var eventActivity = _tracer.StartActivity($"business_event.{eventName}", ActivityKind.Internal))
            {
                if (eventActivity != null)
                {
                    eventActivity.SetTag("event.type", "business_metric");
                    eventActivity.SetTag("event.name", eventName);
                    
                    foreach (var prop in properties)
                    {
                        eventActivity.SetTag($"event.{prop.Key}", prop.Value);
                    }
                }
            }
            
            // Method 3: Create additional processing span for business event
            using (var processActivity = _tracer.StartActivity($"business_process.{eventName}", ActivityKind.Internal))
            {
                if (processActivity != null)
                {
                    var category = eventName.Contains('.') ? eventName.Split('.')[0] : "general";
                    
                    processActivity.SetTag("business.event", eventName);
                    processActivity.SetTag("business.category", category);
                    processActivity.SetTag("process.type", "business_event_processing");
                    
                    foreach (var prop in properties)
                    {
                        processActivity.SetTag($"business.{prop.Key}", prop.Value);
                    }
                    
                    processActivity.AddEvent(new ActivityEvent($"Business event processed: {eventName}"));
                }
            }
            
            // Method 4: Traditional Application Insights (legacy support)
            if (_telemetryClient != null)
            {
                try
                {
                    _telemetryClient.TrackEvent(eventName, properties);
                    _telemetryClient.Flush();
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"⚠️ Application Insights custom event failed: {ex.Message}");
                }
            }
            
            Console.WriteLine($"📊 Business event sent: {eventName} (multiple channels)");
        }
        
        /// <summary>
        /// Record that a transaction was processed.
        /// </summary>
        public void RecordTransactionProcessed(string step, string transactionId)
        {
            if (_transactionCounter != null)
            {
                var tags = new TagList
                {
                    { "step", step },
                    { "transaction_id", transactionId }
                };
                _transactionCounter.Add(1, tags);
            }
        }
        
        /// <summary>
        /// Record risk score distribution.
        /// </summary>
        public void RecordRiskScore(double riskScore, string transactionId, string recommendation)
        {
            if (_riskScoreHistogram != null)
            {
                var tags = new TagList
                {
                    { "transaction_id", transactionId },
                    { "recommendation", recommendation }
                };
                _riskScoreHistogram.Record(riskScore, tags);
            }
        }
        
        /// <summary>
        /// Record compliance decision.
        /// </summary>
        public void RecordComplianceDecision(string decision, string transactionId, Dictionary<string, string> additionalAttributes = null)
        {
            if (_complianceDecisionCounter != null)
            {
                var tags = new TagList
                {
                    { "decision", decision },
                    { "transaction_id", transactionId }
                };
                
                if (additionalAttributes != null)
                {
                    foreach (var attr in additionalAttributes)
                    {
                        tags.Add(attr.Key, attr.Value);
                    }
                }
                
                _complianceDecisionCounter.Add(1, tags);
            }
        }
        
        /// <summary>
        /// Record fraud alert creation.
        /// </summary>
        public void RecordFraudAlertCreated(string alertId, string severity, string decisionAction, string transactionId)
        {
            if (_telemetryClient != null)
            {
                var properties = new Dictionary<string, string>
                {
                    { "alert_id", alertId },
                    { "severity", severity },
                    { "decision_action", decisionAction },
                    { "transaction_id", transactionId },
                    { "timestamp", DateTime.UtcNow.ToString("o") }
                };
                
                _telemetryClient.TrackEvent("FraudAlertCreated", properties);
            }
        }
        
        /// <summary>
        /// Create a span for Cosmos DB operations.
        /// </summary>
        public Activity CreateCosmosSpan(string operation, string collection, Dictionary<string, string> attributes = null)
        {
            var activity = _tracer.StartActivity($"cosmos_db.{collection.ToLower()}.{operation}", ActivityKind.Client);
            
            if (activity != null)
            {
                activity.SetTag("db.operation", operation);
                activity.SetTag("db.collection.name", collection);
                
                if (attributes != null)
                {
                    foreach (var attr in attributes)
                    {
                        activity.SetTag(attr.Key, attr.Value);
                    }
                }
            }
            
            return activity;
        }
        
        /// <summary>
        /// Create a workflow span.
        /// </summary>
        public Activity CreateWorkflowSpan(string workflowName, Dictionary<string, string> attributes = null)
        {
            var activity = _tracer.StartActivity(workflowName, ActivityKind.Client);
            
            if (activity != null)
            {
                activity.SetTag("workflow.name", workflowName);
                activity.SetTag("workflow.version", ServiceVersion);
                
                if (attributes != null)
                {
                    foreach (var attr in attributes)
                    {
                        activity.SetTag(attr.Key, attr.Value);
                    }
                }
            }
            
            return activity;
        }
        
        /// <summary>
        /// Get the current trace ID.
        /// </summary>
        public string GetCurrentTraceId()
        {
            var currentActivity = Activity.Current;
            return currentActivity?.TraceId.ToString();
        }
        
        /// <summary>
        /// Create a detailed operation span with comprehensive attributes.
        /// </summary>
        public Activity CreateDetailedOperationSpan(string operationName, string operationType, Dictionary<string, string> attributes = null)
        {
            var activity = _tracer.StartActivity($"operation.{operationType}.{operationName}", ActivityKind.Internal);
            
            if (activity != null)
            {
                activity.SetTag("operation.name", operationName);
                activity.SetTag("operation.type", operationType);
                activity.SetTag("operation.timestamp", DateTime.UtcNow.ToString("o"));
                
                if (attributes != null)
                {
                    foreach (var attr in attributes)
                    {
                        activity.SetTag(attr.Key, attr.Value);
                    }
                }
            }
            
            return activity;
        }
        
        /// <summary>
        /// Create a span specifically for AI model interactions.
        /// </summary>
        public Activity CreateAiInteractionSpan(string modelName, string operation, Dictionary<string, string> attributes = null)
        {
            var activity = _tracer.StartActivity($"ai_interaction.{modelName}.{operation}", ActivityKind.Client);
            
            if (activity != null)
            {
                activity.SetTag("ai.model", modelName);
                activity.SetTag("ai.operation", operation);
                activity.SetTag("ai.provider", "azure_ai_foundry");
                
                if (attributes != null)
                {
                    foreach (var attr in attributes)
                    {
                        activity.SetTag(attr.Key, attr.Value);
                    }
                }
            }
            
            return activity;
        }
        
        /// <summary>
        /// Create a span for data operations.
        /// </summary>
        public Activity CreateDataOperationSpan(string dataSource, string operation, Dictionary<string, string> attributes = null)
        {
            var activity = _tracer.StartActivity($"data_operation.{dataSource}.{operation}", ActivityKind.Client);
            
            if (activity != null)
            {
                activity.SetTag("data.source", dataSource);
                activity.SetTag("data.operation", operation);
                
                if (attributes != null)
                {
                    foreach (var attr in attributes)
                    {
                        activity.SetTag(attr.Key, attr.Value);
                    }
                }
            }
            
            return activity;
        }
    }
    
    /// <summary>
    /// Instrumentation wrapper for Cosmos DB operations.
    /// </summary>
    public class CosmosDbInstrumentation
    {
        private readonly TelemetryManager _telemetry;
        
        public CosmosDbInstrumentation(TelemetryManager telemetryManager)
        {
            _telemetry = telemetryManager;
        }
        
        /// <summary>
        /// Instrument transaction retrieval with detailed sub-spans.
        /// </summary>
        public async Task<Dictionary<string, object>> InstrumentTransactionGetAsync(
            Func<string, Task<Dictionary<string, object>>> func, 
            string transactionId)
        {
            var attributes = new Dictionary<string, string> { { "transaction.id", transactionId } };
            
            using (var span = _telemetry.CreateCosmosSpan("query", "Transactions", attributes))
            {
                try
                {
                    // Create sub-span for query preparation
                    using (var prepActivity = new ActivitySource(nameof(CosmosDbInstrumentation)).StartActivity("cosmos_db.query_preparation"))
                    {
                        prepActivity?.SetTag("db.operation_type", "select_by_id");
                        prepActivity?.SetTag("db.query_target", "transaction");
                        prepActivity?.AddEvent(new ActivityEvent("Query preparation started"));
                    }
                    
                    // Create sub-span for query execution
                    Dictionary<string, object> result;
                    using (var execActivity = new ActivitySource(nameof(CosmosDbInstrumentation)).StartActivity("cosmos_db.query_execution"))
                    {
                        execActivity?.SetTag("db.statement_type", "SELECT");
                        execActivity?.SetTag("db.collection", "Transactions");
                        execActivity?.AddEvent(new ActivityEvent("Executing transaction query"));
                        
                        result = await func(transactionId);
                        
                        execActivity?.AddEvent(new ActivityEvent("Query execution completed"));
                    }
                    
                    // Create sub-span for result processing
                    using (var resultActivity = new ActivitySource(nameof(CosmosDbInstrumentation)).StartActivity("cosmos_db.result_processing"))
                    {
                        var hasError = result.ContainsKey("error");
                        resultActivity?.SetTag("db.result_type", "transaction_data");
                        resultActivity?.SetTag("db.success", !hasError);
                        
                        if (!hasError)
                        {
                            span?.SetTag("transaction.amount", result.GetValueOrDefault("amount", 0));
                            span?.SetTag("transaction.currency", result.GetValueOrDefault("currency", ""));
                            span?.SetTag("transaction.destination", result.GetValueOrDefault("destination_country", ""));
                            span?.SetTag("cosmos_db.success", true);
                            resultActivity?.AddEvent(new ActivityEvent("Transaction data parsed successfully"));
                        }
                        else
                        {
                            span?.SetTag("cosmos_db.success", false);
                            span?.SetTag("cosmos_db.error", result["error"]);
                            resultActivity?.AddEvent(new ActivityEvent("Transaction retrieval failed"));
                        }
                    }
                    
                    return result;
                }
                catch (Exception ex)
                {
                    span?.SetTag("cosmos_db.success", false);
                    span?.SetTag("cosmos_db.error", ex.Message);
                    span?.AddEvent(new ActivityEvent("Exception", tags: new ActivityTagsCollection
                    {
                        { "exception.type", ex.GetType().FullName },
                        { "exception.message", ex.Message }
                    }));
                    
                    return new Dictionary<string, object> { { "error", ex.Message } };
                }
            }
        }
        
        /// <summary>
        /// Instrument customer retrieval with detailed sub-spans.
        /// </summary>
        public async Task<Dictionary<string, object>> InstrumentCustomerGetAsync(
            Func<string, Task<Dictionary<string, object>>> func,
            string customerId)
        {
            var attributes = new Dictionary<string, string> { { "customer.id", customerId } };
            
            using (var span = _telemetry.CreateCosmosSpan("query", "Customers", attributes))
            {
                try
                {
                    // Create sub-span for customer query preparation
                    using (var prepActivity = new ActivitySource(nameof(CosmosDbInstrumentation)).StartActivity("cosmos_db.customer_query_prep"))
                    {
                        prepActivity?.SetTag("db.operation_type", "select_customer_by_id");
                        prepActivity?.SetTag("customer.lookup_id", customerId);
                        prepActivity?.AddEvent(new ActivityEvent("Customer query preparation started"));
                    }
                    
                    // Create sub-span for customer query execution
                    Dictionary<string, object> result;
                    using (var execActivity = new ActivitySource(nameof(CosmosDbInstrumentation)).StartActivity("cosmos_db.customer_query_exec"))
                    {
                        execActivity?.SetTag("db.statement_type", "SELECT");
                        execActivity?.SetTag("db.collection", "Customers");
                        execActivity?.AddEvent(new ActivityEvent("Executing customer query"));
                        
                        result = await func(customerId);
                        
                        execActivity?.AddEvent(new ActivityEvent("Customer query execution completed"));
                    }
                    
                    // Create sub-span for customer data processing
                    using (var processActivity = new ActivitySource(nameof(CosmosDbInstrumentation)).StartActivity("cosmos_db.customer_data_processing"))
                    {
                        var hasError = result.ContainsKey("error");
                        processActivity?.SetTag("db.result_type", "customer_profile");
                        processActivity?.SetTag("db.success", !hasError);
                        
                        if (!hasError)
                        {
                            span?.SetTag("customer.country", result.GetValueOrDefault("country", ""));
                            span?.SetTag("customer.account_age", result.GetValueOrDefault("account_age_days", 0));
                            span?.SetTag("customer.device_trust_score", result.GetValueOrDefault("device_trust_score", 0));
                            span?.SetTag("customer.past_fraud", result.GetValueOrDefault("past_fraud", false));
                            span?.SetTag("cosmos_db.success", true);
                            processActivity?.AddEvent(new ActivityEvent("Customer profile processed successfully"));
                        }
                        else
                        {
                            span?.SetTag("cosmos_db.success", false);
                            span?.SetTag("cosmos_db.error", result["error"]);
                            processActivity?.AddEvent(new ActivityEvent("Customer retrieval failed"));
                        }
                    }
                    
                    return result;
                }
                catch (Exception ex)
                {
                    span?.SetTag("cosmos_db.success", false);
                    span?.SetTag("cosmos_db.error", ex.Message);
                    span?.AddEvent(new ActivityEvent("Exception", tags: new ActivityTagsCollection
                    {
                        { "exception.type", ex.GetType().FullName },
                        { "exception.message", ex.Message }
                    }));
                    
                    return new Dictionary<string, object> { { "error", ex.Message } };
                }
            }
        }
        
        /// <summary>
        /// Instrument transaction list retrieval.
        /// </summary>
        public async Task<List<Dictionary<string, object>>> InstrumentTransactionListAsync(
            Func<string, Task<List<Dictionary<string, object>>>> func,
            string customerId)
        {
            var attributes = new Dictionary<string, string> { { "customer.id", customerId } };
            
            using (var span = _telemetry.CreateCosmosSpan("query", "Transactions", attributes))
            {
                try
                {
                    var result = await func(customerId);
                    
                    if (result != null && result.Count > 0 && !result[0].ContainsKey("error"))
                    {
                        span?.SetTag("transaction.count", result.Count);
                        span?.SetTag("cosmos_db.success", true);
                    }
                    else
                    {
                        span?.SetTag("cosmos_db.success", false);
                        span?.SetTag("cosmos_db.error", "Failed to retrieve transactions");
                    }
                    
                    return result;
                }
                catch (Exception ex)
                {
                    span?.SetTag("cosmos_db.success", false);
                    span?.SetTag("cosmos_db.error", ex.Message);
                    span?.AddEvent(new ActivityEvent("Exception", tags: new ActivityTagsCollection
                    {
                        { "exception.type", ex.GetType().FullName },
                        { "exception.message", ex.Message }
                    }));
                    
                    return new List<Dictionary<string, object>> { new Dictionary<string, object> { { "error", ex.Message } } };
                }
            }
        }
    }
    
    /// <summary>
    /// Global telemetry instance helper class.
    /// </summary>
    public static class GlobalTelemetry
    {
        private static readonly Lazy<TelemetryManager> _instance = new Lazy<TelemetryManager>(() => new TelemetryManager());
        
        public static TelemetryManager Instance => _instance.Value;
        
        public static void InitializeTelemetry()
        {
            Instance.InitializeObservability();
        }
        
        public static TelemetryManager GetTelemetryManager()
        {
            return Instance;
        }
        
        public static void SendBusinessEvent(string eventName, Dictionary<string, string> properties)
        {
            Instance.SendBusinessEvent(eventName, properties);
        }
        
        public static void FlushTelemetry()
        {
            Instance.FlushTelemetry();
        }
        
        public static string GetCurrentTraceId()
        {
            return Instance.GetCurrentTraceId();
        }
    }
}
