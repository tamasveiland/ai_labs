namespace AgentToolsApi.Models;

public class OrderDetails
{
    public string Id { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string DeliveryDate { get; set; } = string.Empty;
    public List<string> Items { get; set; } = new();
    public decimal Total { get; set; }
}

public class OrderResponse
{
    public OrderDetails? Order { get; set; }
    public string? Error { get; set; }
}

public class TrackingInfo
{
    public string TrackingNumber { get; set; } = string.Empty;
    public string Carrier { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string EstimatedDelivery { get; set; } = string.Empty;
}

public class TrackingResponse
{
    public TrackingInfo? TrackingInfo { get; set; }
    public string? Error { get; set; }
}

public class EiffelTowerResponse
{
    public string Info { get; set; } = string.Empty;
}
