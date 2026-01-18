using Microsoft.AspNetCore.Mvc;
using AgentToolsApi.Models;

namespace AgentToolsApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class TrackingController : ControllerBase
{
    private readonly ILogger<TrackingController> _logger;

    // Simulated tracking database
    private static readonly Dictionary<string, TrackingInfo> TrackingData = new()
    {
        ["123"] = new TrackingInfo
        {
            TrackingNumber = "ABC123",
            Carrier = "UPS",
            Status = "In Transit",
            EstimatedDelivery = "2025-03-15"
        },
        ["456"] = new TrackingInfo
        {
            TrackingNumber = "XYZ789",
            Carrier = "FedEx",
            Status = "Processing",
            EstimatedDelivery = "2025-03-20"
        }
    };

    public TrackingController(ILogger<TrackingController> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// Get tracking information for an order
    /// </summary>
    /// <param name="orderId">The order ID to track</param>
    /// <returns>Tracking information or error message</returns>
    [HttpGet("{orderId}")]
    [ProducesResponseType(typeof(TrackingResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public ActionResult<TrackingResponse> GetTracking(string orderId)
    {
        _logger.LogInformation("Getting tracking information for order ID: {OrderId}", orderId);

        if (TrackingData.TryGetValue(orderId, out var tracking))
        {
            return Ok(new TrackingResponse { TrackingInfo = tracking });
        }

        return NotFound(new TrackingResponse { Error = "Tracking not found" });
    }
}
