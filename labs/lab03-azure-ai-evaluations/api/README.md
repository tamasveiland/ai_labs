# Agent Tools API

This is a C# .NET 8 Web API that provides endpoints for Azure AI agent tools. The API is designed to be hosted on Azure App Service (Basic Plan).

## Endpoints

### 1. Order Information
**GET** `/api/order/{orderId}`

Retrieves details about a specific order.

**Example:**
```bash
curl https://your-api.azurewebsites.net/api/order/123
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

### 2. Tracking Information
**GET** `/api/tracking/{orderId}`

Retrieves tracking information for an order.

**Example:**
```bash
curl https://your-api.azurewebsites.net/api/tracking/123
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

### 3. Eiffel Tower Information
**GET** `/api/eiffeltower?infoType={type}`

Retrieves information about the Eiffel Tower.

**Query Parameters:**
- `infoType` (optional): Type of information - `hours`, `tickets`, or `location` (default: `hours`)

**Example:**
```bash
curl https://your-api.azurewebsites.net/api/eiffeltower?infoType=hours
```

**Response:**
```json
{
  "info": "Opening hours of the Eiffel Tower are 9:00 AM to 11:00 PM."
}
```

## Local Development

### Prerequisites
- .NET 8.0 SDK
- Visual Studio Code or Visual Studio

### Running Locally

1. Navigate to the API directory:
```bash
cd labs/lab03-azure-ai-evaluations/api/AgentToolsApi
```

2. Run the application:
```bash
dotnet run
```

3. Access Swagger UI at: `http://localhost:5000/swagger`

## Deployment

The API is deployed to Azure App Service as part of the lab infrastructure using Bicep.

### Deploy with azd

```bash
cd labs/lab03-azure-ai-evaluations
azd up
```

The API will be deployed and the URL will be available in the output as `AGENT_TOOLS_API_URI`.

### Manual Deployment

```bash
# Build the project
dotnet publish -c Release -o ./publish

# Deploy to Azure (using Azure CLI)
az webapp deployment source config-zip \
  --resource-group <resource-group-name> \
  --name <app-service-name> \
  --src ./publish.zip
```

## Integration with AI Agents

To use these endpoints with Azure AI agents, configure the agent's tools to call the API endpoints:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Get details of a specific order",
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
```

Then implement the function to call the API:

```python
import requests

def get_order(order_id: str) -> str:
    response = requests.get(f"{api_base_url}/api/order/{order_id}")
    return response.text
```

## Architecture

The API is hosted on:
- **Azure App Service** (Basic B1 plan)
- **Linux** runtime
- **.NET 8.0** framework

It includes:
- Application Insights for monitoring
- CORS enabled for cross-origin requests
- Swagger/OpenAPI documentation
- HTTPS enforcement
