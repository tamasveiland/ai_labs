using Microsoft.AspNetCore.Mvc;
using AgentToolsApi.Models;

namespace AgentToolsApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class EiffelTowerController : ControllerBase
{
    private readonly ILogger<EiffelTowerController> _logger;

    // Simulated Eiffel Tower information
    private static readonly Dictionary<string, string> EiffelTowerInfo = new()
    {
        ["hours"] = "Opening hours of the Eiffel Tower are 9:00 AM to 11:00 PM.",
        ["tickets"] = "Tickets range from €10-€25 depending on access level.",
        ["location"] = "Champ de Mars, 5 Avenue Anatole France, 75007 Paris, France"
    };

    public EiffelTowerController(ILogger<EiffelTowerController> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// Get information about the Eiffel Tower
    /// </summary>
    /// <param name="infoType">Type of information: hours, tickets, or location (default: hours)</param>
    /// <returns>Requested information</returns>
    [HttpGet]
    [ProducesResponseType(typeof(EiffelTowerResponse), StatusCodes.Status200OK)]
    public ActionResult<EiffelTowerResponse> GetInfo([FromQuery] string infoType = "hours")
    {
        _logger.LogInformation("Getting Eiffel Tower information for type: {InfoType}", infoType);

        var info = EiffelTowerInfo.TryGetValue(infoType.ToLower(), out var value)
            ? value
            : "Information not available";

        return Ok(new EiffelTowerResponse { Info = info });
    }
}
