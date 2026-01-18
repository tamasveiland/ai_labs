# Agent Tools API - Quick Reference

## API Base URL
```
https://<app-name>.azurewebsites.net
```

## Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/api/order/{orderId}` | GET | `orderId` (path) | Get order details |
| `/api/tracking/{orderId}` | GET | `orderId` (path) | Get tracking info |
| `/api/eiffeltower` | GET | `infoType` (query) | Get Eiffel Tower info |

## Example Requests

### cURL

```bash
# Get order
curl https://your-api.azurewebsites.net/api/order/123

# Get tracking
curl https://your-api.azurewebsites.net/api/tracking/123

# Get Eiffel Tower info
curl "https://your-api.azurewebsites.net/api/eiffeltower?infoType=hours"
```

### Python

```python
import requests

base_url = "https://your-api.azurewebsites.net"

# Get order
response = requests.get(f"{base_url}/api/order/123")
print(response.json())

# Get tracking
response = requests.get(f"{base_url}/api/tracking/123")
print(response.json())

# Get Eiffel Tower info
response = requests.get(f"{base_url}/api/eiffeltower", params={"infoType": "hours"})
print(response.json())
```

### PowerShell

```powershell
$baseUrl = "https://your-api.azurewebsites.net"

# Get order
Invoke-RestMethod -Uri "$baseUrl/api/order/123"

# Get tracking
Invoke-RestMethod -Uri "$baseUrl/api/tracking/123"

# Get Eiffel Tower info
Invoke-RestMethod -Uri "$baseUrl/api/eiffeltower?infoType=hours"
```

## Sample Data

### Available Orders
- `123` - Shipped order with 2 items
- `456` - Processing order with 1 item

### Eiffel Tower Info Types
- `hours` - Opening hours
- `tickets` - Ticket pricing
- `location` - Address

## Response Examples

### Order Response
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

### Tracking Response
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

### Eiffel Tower Response
```json
{
  "info": "Opening hours of the Eiffel Tower are 9:00 AM to 11:00 PM."
}
```

## Error Responses

### 404 Not Found
```json
{
  "error": "Order not found"
}
```

## Environment Setup

### Set API URL in .env
```bash
AGENT_TOOLS_API_URI=https://your-api.azurewebsites.net
```

### Get API URL from azd
```bash
azd env get-values | grep AGENT_TOOLS_API_URI
```

## Swagger Documentation
```
https://your-api.azurewebsites.net/swagger
```

## Monitoring

### Stream Logs
```bash
az webapp log tail --name <app-name> --resource-group <rg-name>
```

### View in Portal
1. Go to Azure Portal
2. Navigate to App Service
3. Select "Log stream" or "Application Insights"

## Common Commands

```bash
# Deploy
azd up

# Get outputs
azd env get-values

# View logs
az webapp log tail -g <rg> -n <app-name>

# Restart app
az webapp restart -g <rg> -n <app-name>

# Delete resources
azd down --purge
```
