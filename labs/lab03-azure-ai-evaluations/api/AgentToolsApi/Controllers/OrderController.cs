using Microsoft.AspNetCore.Mvc;
using AgentToolsApi.Models;

namespace AgentToolsApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class OrderController : ControllerBase
{
    private readonly ILogger<OrderController> _logger;

    // Simulated order database
    private static readonly Dictionary<string, OrderDetails> Orders = new()
    {
        ["123"] = new OrderDetails
        {
            Id = "123",
            Status = "shipped",
            DeliveryDate = "2025-03-15",
            Items = new List<string> { "Widget A", "Widget B" },
            Total = 99.99m
        },
        ["456"] = new OrderDetails
        {
            Id = "456",
            Status = "processing",
            DeliveryDate = "2025-03-20",
            Items = new List<string> { "Gadget X" },
            Total = 49.99m
        }
    };

    public OrderController(ILogger<OrderController> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// Get the details of a specific order
    /// </summary>
    /// <param name="orderId">The order ID to retrieve</param>
    /// <returns>Order details or error message</returns>
    [HttpGet("{orderId}")]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public ActionResult<OrderResponse> GetOrder(string orderId)
    {
        _logger.LogInformation("Getting order details for order ID: {OrderId}", orderId);

        if (Orders.TryGetValue(orderId, out var order))
        {
            return Ok(new OrderResponse { Order = order });
        }

        return NotFound(new OrderResponse { Error = "Order not found" });
    }
}
