# Agent Tools API Integration Guide

## Overview

The Agent Tools API is a C# .NET 8 Web API that provides three endpoints for Azure AI agent tools:
- **Order Information**: Retrieve order details
- **Tracking Information**: Get shipping/tracking information
- **Eiffel Tower Information**: Tourist information about the Eiffel Tower

These endpoints replace the local Python functions previously used in the agent evaluation examples.

## Architecture

```
┌─────────────────────┐
│   Azure AI Agent    │
│                     │
│  ┌──────────────┐   │
│  │ Agent Tools  │   │      HTTPS
│  │  (Functions) │   ├─────────────────┐
│  └──────────────┘   │                 │
└─────────────────────┘                 │
                                        ▼
                              ┌──────────────────────┐
                              │  Azure App Service   │
                              │  (Basic B1 Plan)     │
                              │                      │
                              │  Agent Tools API     │
                              │  - .NET 8 Runtime    │
                              │  - Linux Container   │
                              │                      │
                              │  Endpoints:          │
                              │  /api/order/{id}     │
                              │  /api/tracking/{id}  │
                              │  /api/eiffeltower    │
                              └──────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────────┐
                              │ Application Insights │
                              │   (Monitoring)       │
                              └──────────────────────┘
```

## Infrastructure Components

### 1. App Service Plan (Basic B1)
- **SKU**: B1 (Basic tier)
- **OS**: Linux
- **Pricing**: ~$13/month
- **Features**:
  - 1 GB RAM
  - 1 Core
  - Custom domains
  - SSL/TLS support
  - Always On capability

### 2. App Service
- **Runtime**: .NET 8.0
- **Platform**: Linux
- **Features**:
  - HTTPS enforcement
  - CORS enabled
  - System-assigned managed identity
  - Application Insights integration
  - Swagger/OpenAPI documentation

### 3. Application Insights
- Request tracking
- Dependency tracking
- Exception monitoring
- Performance metrics

## API Endpoints

### 1. GET /api/order/{orderId}

Retrieves order details.

**Request:**
```http
GET /api/order/123 HTTP/1.1
Host: app-xxx.azurewebsites.net
```

**Response:**
```json
{
  "order": {
    "id": "123",
    "status": "shipped",
    "deliveryDate": "2025-03-15",
    "items": ["Widget A", "Widget B"],
    "total": 99.99
  }
}
```

### 2. GET /api/tracking/{orderId}

Retrieves tracking information.

**Request:**
```http
GET /api/tracking/123 HTTP/1.1
Host: app-xxx.azurewebsites.net
```

**Response:**
```json
{
  "trackingInfo": {
    "trackingNumber": "ABC123",
    "carrier": "UPS",
    "status": "In Transit",
    "estimatedDelivery": "2025-03-15"
  }
}
```

### 3. GET /api/eiffeltower

Retrieves Eiffel Tower information.

**Request:**
```http
GET /api/eiffeltower?infoType=hours HTTP/1.1
Host: app-xxx.azurewebsites.net
```

**Query Parameters:**
- `infoType`: `hours`, `tickets`, or `location` (default: `hours`)

**Response:**
```json
{
  "info": "Opening hours of the Eiffel Tower are 9:00 AM to 11:00 PM."
}
```

## Integration with Azure AI Agents

### Before: Local Python Functions

```python
def get_order(order_id: str) -> str:
    orders = {
        "123": {
            "id": "123",
            "status": "shipped",
            # ...
        }
    }
    return json.dumps({"order": orders.get(order_id)})
```

### After: API Integration

```python
import requests

API_BASE_URL = os.getenv("AGENT_TOOLS_API_URI")

def get_order(order_id: str) -> str:
    response = requests.get(f"{API_BASE_URL}/api/order/{order_id}")
    return response.text
```

### Agent Configuration

When creating an agent, use the same tool definitions:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Get the details of a specific order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID"
                    }
                },
                "required": ["order_id"]
            }
        }
    }
]

agent = project_client.agents.create(
    model=model_deployment_name,
    name="customer_service_agent",
    instructions="You are a helpful customer service agent...",
    tools=tools
)
```

### Handling Tool Calls

```python
# When the agent makes a tool call
if response.tool_calls:
    for tool_call in response.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        # Execute the API call
        if function_name == "get_order":
            result = get_order(**arguments)
        elif function_name == "get_tracking":
            result = get_tracking(**arguments)
        elif function_name == "get_eiffel_tower_info":
            result = get_eiffel_tower_info(**arguments)
```

## Benefits of API-Based Tools

### 1. Separation of Concerns
- Agent logic separated from data/business logic
- Easier to maintain and update
- Multiple agents can share the same tools

### 2. Scalability
- App Service can scale independently
- Can handle multiple concurrent requests
- Better resource utilization

### 3. Security
- Centralized authentication/authorization
- API keys, managed identities, or OAuth
- Request validation and rate limiting

### 4. Monitoring
- Centralized logging in Application Insights
- Request/response tracking
- Performance metrics and alerts

### 5. Flexibility
- Easy to add new endpoints
- Version management
- A/B testing capabilities

### 6. Language Agnostic
- Python agents can call C# API
- JavaScript, Java, or any language that supports HTTP

## Deployment

### Using Azure Developer CLI (azd)

```bash
cd labs/lab03-azure-ai-evaluations
azd up
```

The infrastructure (Bicep) will:
1. Create a resource group
2. Deploy App Service Plan (B1)
3. Deploy App Service
4. Configure Application Insights
5. Deploy the .NET API code

### Output Variables

After deployment, these outputs are available:

```bash
# Get API URL
azd env get-values | grep AGENT_TOOLS_API_URI

# Use in Python
export AGENT_TOOLS_API_URI=$(azd env get-values | grep AGENT_TOOLS_API_URI | cut -d'=' -f2)
```

## Testing

### 1. Test API Directly

```bash
API_URL="https://your-api.azurewebsites.net"

# Test order endpoint
curl $API_URL/api/order/123

# Test tracking endpoint
curl $API_URL/api/tracking/123

# Test Eiffel Tower endpoint
curl "$API_URL/api/eiffeltower?infoType=hours"
```

### 2. Test with Python Script

```bash
cd labs/lab03-azure-ai-evaluations/evaluations/agentic_evaluators

# Set API URL
export AGENT_TOOLS_API_URI="https://your-api.azurewebsites.net"

# Run test script
python api_integration_example.py
```

### 3. Access Swagger UI

```
https://your-api.azurewebsites.net/swagger
```

## Updating the Agent Evaluation Script

To use the API in your agent evaluations:

1. **Set the API URL**:
```python
import os
os.environ["AGENT_TOOLS_API_URI"] = "https://your-api.azurewebsites.net"
```

2. **Replace function implementations**:
```python
from api_integration_example import get_order, get_tracking, get_eiffel_tower_info
```

3. **Run evaluation as before**:
```python
python sample_intent_resolution_live.py
```

## Cost Estimation

**Monthly Costs (Basic B1 Plan):**
- App Service Plan B1: ~$13/month
- Application Insights: Free tier (first 5 GB/month)
- Bandwidth: Minimal (within free tier for testing)

**Total: ~$13-15/month**

## Security Considerations

### 1. Enable Authentication (Optional)

```bash
az webapp auth update \
  --resource-group <rg-name> \
  --name <app-name> \
  --enabled true \
  --action LoginWithAzureActiveDirectory
```

### 2. Restrict CORS Origins

Update [Program.cs](./AgentToolsApi/Program.cs):

```csharp
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowSpecificOrigin", policy =>
    {
        policy.WithOrigins("https://yourdomain.com")
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});
```

### 3. Add API Key Validation

Implement middleware for API key validation:

```csharp
app.Use(async (context, next) =>
{
    var apiKey = context.Request.Headers["X-API-Key"];
    if (apiKey != expectedApiKey)
    {
        context.Response.StatusCode = 401;
        return;
    }
    await next();
});
```

## Monitoring and Troubleshooting

### View Logs

```bash
az webapp log tail \
  --resource-group <rg-name> \
  --name <app-name>
```

### Application Insights Queries

```kusto
// Failed requests
requests
| where success == false
| project timestamp, name, resultCode, duration

// Top 10 slowest requests
requests
| top 10 by duration desc
| project timestamp, name, duration, url
```

## Next Steps

1. **Add Authentication**: Implement Azure AD or API key authentication
2. **Add Database**: Connect to Azure SQL or Cosmos DB for real data
3. **Add Caching**: Implement Redis cache for frequently accessed data
4. **Add Rate Limiting**: Protect against abuse
5. **CI/CD Pipeline**: Set up GitHub Actions for automated deployments
6. **Custom Domain**: Configure a custom domain with SSL
7. **API Management**: Add Azure API Management for advanced features

## References

- [Agent Tools API README](./api/README.md)
- [Deployment Guide](./api/DEPLOYMENT.md)
- [API Integration Example](./evaluations/agentic_evaluators/api_integration_example.py)
- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure AI Agents Documentation](https://docs.microsoft.com/azure/ai-services/agents/)
