using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using FraudDetectionWorkflow.Telemetry;

namespace FraudDetectionWorkflow.Examples
{
    /// <summary>
    /// Example usage of the Telemetry module for fraud detection workflow
    /// </summary>
    public class TelemetryUsageExample
    {
        public static async Task Main(string[] args)
        {
            // Initialize telemetry at application startup
            GlobalTelemetry.InitializeTelemetry();
            
            // Get the telemetry manager instance
            var telemetryManager = GlobalTelemetry.GetTelemetryManager();
            
            // Example 1: Create a workflow span
            await ProcessTransactionWorkflowAsync(telemetryManager);
            
            // Example 2: Send business events
            SendBusinessEventsExample(telemetryManager);
            
            // Example 3: Record metrics
            RecordMetricsExample(telemetryManager);
            
            // Example 4: Cosmos DB instrumentation
            await CosmosDbInstrumentationExample(telemetryManager);
            
            // Flush telemetry before application exit
            GlobalTelemetry.FlushTelemetry();
            
            Console.WriteLine("Telemetry examples completed!");
        }
        
        /// <summary>
        /// Example of creating a workflow span with nested operations
        /// </summary>
        private static async Task ProcessTransactionWorkflowAsync(TelemetryManager telemetry)
        {
            var workflowAttributes = new Dictionary<string, string>
            {
                { "transaction.id", "TXN-12345" },
                { "customer.id", "CUST-67890" }
            };
            
            // Create workflow span
            using (var workflowActivity = telemetry.CreateWorkflowSpan("fraud_detection_workflow", workflowAttributes))
            {
                Console.WriteLine($"Workflow started with trace ID: {telemetry.GetCurrentTraceId()}");
                
                // Step 1: Risk Analysis
                using (var riskActivity = telemetry.CreateDetailedOperationSpan(
                    "analyze_risk", 
                    "risk_analysis",
                    new Dictionary<string, string> { { "transaction.id", "TXN-12345" } }))
                {
                    await Task.Delay(100); // Simulate processing
                    Console.WriteLine("Risk analysis completed");
                    
                    // Record risk score metric
                    telemetry.RecordRiskScore(0.75, "TXN-12345", "high_risk");
                }
                
                // Step 2: Customer Data Retrieval
                using (var customerActivity = telemetry.CreateDataOperationSpan(
                    "cosmos_db",
                    "get_customer",
                    new Dictionary<string, string> { { "customer.id", "CUST-67890" } }))
                {
                    await Task.Delay(50); // Simulate processing
                    Console.WriteLine("Customer data retrieved");
                }
                
                // Step 3: AI Model Interaction
                using (var aiActivity = telemetry.CreateAiInteractionSpan(
                    "gpt-4o",
                    "compliance_check",
                    new Dictionary<string, string> 
                    { 
                        { "prompt.tokens", "500" },
                        { "completion.tokens", "200" }
                    }))
                {
                    await Task.Delay(200); // Simulate AI processing
                    Console.WriteLine("AI compliance check completed");
                }
                
                // Step 4: Record transaction processed
                telemetry.RecordTransactionProcessed("workflow_complete", "TXN-12345");
                
                Console.WriteLine("Workflow completed successfully");
            }
        }
        
        /// <summary>
        /// Example of sending business events
        /// </summary>
        private static void SendBusinessEventsExample(TelemetryManager telemetry)
        {
            // Send a fraud detection event
            var fraudEventProperties = new Dictionary<string, string>
            {
                { "transaction_id", "TXN-12345" },
                { "risk_score", "0.85" },
                { "decision", "block" },
                { "reason", "high_risk_country" }
            };
            
            telemetry.SendBusinessEvent("fraud_detection.high_risk_transaction", fraudEventProperties);
            
            // Send a compliance violation event
            var complianceEventProperties = new Dictionary<string, string>
            {
                { "transaction_id", "TXN-12345" },
                { "regulation", "AML" },
                { "violation_type", "suspicious_pattern" },
                { "severity", "critical" }
            };
            
            telemetry.SendBusinessEvent("compliance.violation_detected", complianceEventProperties);
            
            Console.WriteLine("Business events sent");
        }
        
        /// <summary>
        /// Example of recording metrics
        /// </summary>
        private static void RecordMetricsExample(TelemetryManager telemetry)
        {
            // Record transactions processed
            for (int i = 0; i < 5; i++)
            {
                telemetry.RecordTransactionProcessed("risk_analysis", $"TXN-{i}");
                telemetry.RecordTransactionProcessed("compliance_check", $"TXN-{i}");
            }
            
            // Record risk scores
            var riskScores = new[] { 0.2, 0.45, 0.67, 0.89, 0.95 };
            var recommendations = new[] { "approve", "review", "review", "block", "block" };
            
            for (int i = 0; i < riskScores.Length; i++)
            {
                telemetry.RecordRiskScore(riskScores[i], $"TXN-{i}", recommendations[i]);
            }
            
            // Record compliance decisions
            telemetry.RecordComplianceDecision("approved", "TXN-0");
            telemetry.RecordComplianceDecision("flagged_for_review", "TXN-1");
            telemetry.RecordComplianceDecision("blocked", "TXN-2", new Dictionary<string, string>
            {
                { "regulation", "AML" },
                { "reason", "high_risk" }
            });
            
            // Record fraud alert
            telemetry.RecordFraudAlertCreated(
                alertId: "ALERT-12345",
                severity: "critical",
                decisionAction: "block_transaction",
                transactionId: "TXN-12345"
            );
            
            Console.WriteLine("Metrics recorded");
        }
        
        /// <summary>
        /// Example of Cosmos DB instrumentation
        /// </summary>
        private static async Task CosmosDbInstrumentationExample(TelemetryManager telemetry)
        {
            var cosmosInstrumentation = new CosmosDbInstrumentation(telemetry);
            
            // Example 1: Instrument transaction retrieval
            var transaction = await cosmosInstrumentation.InstrumentTransactionGetAsync(
                async (transactionId) =>
                {
                    // Simulate Cosmos DB query
                    await Task.Delay(50);
                    return new Dictionary<string, object>
                    {
                        { "id", transactionId },
                        { "amount", 5000.00 },
                        { "currency", "USD" },
                        { "destination_country", "US" },
                        { "timestamp", DateTime.UtcNow }
                    };
                },
                "TXN-12345"
            );
            
            Console.WriteLine($"Retrieved transaction: {transaction["id"]}");
            
            // Example 2: Instrument customer retrieval
            var customer = await cosmosInstrumentation.InstrumentCustomerGetAsync(
                async (customerId) =>
                {
                    // Simulate Cosmos DB query
                    await Task.Delay(50);
                    return new Dictionary<string, object>
                    {
                        { "id", customerId },
                        { "country", "US" },
                        { "account_age_days", 365 },
                        { "device_trust_score", 0.95 },
                        { "past_fraud", false }
                    };
                },
                "CUST-67890"
            );
            
            Console.WriteLine($"Retrieved customer: {customer["id"]}");
            
            // Example 3: Instrument transaction list retrieval
            var transactions = await cosmosInstrumentation.InstrumentTransactionListAsync(
                async (customerId) =>
                {
                    // Simulate Cosmos DB query
                    await Task.Delay(75);
                    return new List<Dictionary<string, object>>
                    {
                        new Dictionary<string, object>
                        {
                            { "id", "TXN-001" },
                            { "amount", 100.00 },
                            { "timestamp", DateTime.UtcNow.AddDays(-1) }
                        },
                        new Dictionary<string, object>
                        {
                            { "id", "TXN-002" },
                            { "amount", 250.00 },
                            { "timestamp", DateTime.UtcNow.AddDays(-2) }
                        }
                    };
                },
                "CUST-67890"
            );
            
            Console.WriteLine($"Retrieved {transactions.Count} transactions for customer");
        }
        
        /// <summary>
        /// Example of error handling with telemetry
        /// </summary>
        private static async Task ErrorHandlingExample(TelemetryManager telemetry)
        {
            using (var activity = telemetry.CreateDetailedOperationSpan("risky_operation", "data_processing"))
            {
                try
                {
                    // Simulate an operation that might fail
                    await Task.Delay(10);
                    throw new InvalidOperationException("Simulated error");
                }
                catch (Exception ex)
                {
                    // Record the exception in telemetry
                    activity?.SetTag("error", true);
                    activity?.SetTag("error.type", ex.GetType().Name);
                    activity?.SetTag("error.message", ex.Message);
                    
                    // Send a business event for the error
                    telemetry.SendBusinessEvent("operation.failed", new Dictionary<string, string>
                    {
                        { "operation", "risky_operation" },
                        { "error_type", ex.GetType().Name },
                        { "error_message", ex.Message }
                    });
                    
                    Console.WriteLine($"Error handled and recorded: {ex.Message}");
                }
            }
        }
    }
}
