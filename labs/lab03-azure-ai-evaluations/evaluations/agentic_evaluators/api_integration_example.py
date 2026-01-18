"""
Example showing how to integrate the Agent Tools API with Azure AI agents.
This replaces the local Python functions with HTTP calls to the deployed API.
"""

import os
import json
import requests
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

# Get API base URL from environment or use default
API_BASE_URL = os.getenv("AGENT_TOOLS_API_URI", "https://your-api.azurewebsites.net")


def get_order(order_id: str) -> str:
    """
    Get the details of a specific order by calling the API.
    
    Args:
        order_id: The order ID to retrieve
        
    Returns:
        JSON string with order details or error
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/order/{order_id}",
            timeout=30
        )
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Failed to get order: {str(e)}"})


def get_tracking(order_id: str) -> str:
    """
    Get tracking information for an order by calling the API.
    
    Args:
        order_id: The order ID to get tracking for
        
    Returns:
        JSON string with tracking information or error
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/tracking/{order_id}",
            timeout=30
        )
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Failed to get tracking: {str(e)}"})


def get_eiffel_tower_info(info_type: str = "hours") -> str:
    """
    Get information about the Eiffel Tower by calling the API.
    
    Args:
        info_type: Type of information - 'hours', 'tickets', or 'location'
        
    Returns:
        JSON string with requested information
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/eiffeltower",
            params={"infoType": info_type},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("info", "Information not available")
    except requests.exceptions.RequestException as e:
        return f"Failed to get Eiffel Tower info: {str(e)}"


# Tool definitions for Azure AI agents
TOOL_DEFINITIONS = [
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
                        "description": "The order ID to get the details for."
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tracking",
            "description": "Get tracking information for an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to get tracking for."
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_eiffel_tower_info",
            "description": "Get information about the Eiffel Tower.",
            "parameters": {
                "type": "object",
                "properties": {
                    "info_type": {
                        "type": "string",
                        "description": "Type of information: 'hours', 'tickets', or 'location'",
                        "enum": ["hours", "tickets", "location"]
                    }
                }
            }
        }
    }
]


# Function mapping for tool execution
AVAILABLE_FUNCTIONS = {
    "get_order": get_order,
    "get_tracking": get_tracking,
    "get_eiffel_tower_info": get_eiffel_tower_info
}


def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a tool call by name with the provided arguments.
    
    Args:
        tool_name: Name of the tool/function to call
        arguments: Dictionary of arguments to pass to the function
        
    Returns:
        Result from the function call
    """
    if tool_name in AVAILABLE_FUNCTIONS:
        function = AVAILABLE_FUNCTIONS[tool_name]
        try:
            return function(**arguments)
        except Exception as e:
            return json.dumps({"error": f"Error executing {tool_name}: {str(e)}"})
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


def test_api_endpoints():
    """Test all API endpoints to verify they're working."""
    print(f"Testing API at: {API_BASE_URL}\n")
    
    # Test 1: Get order
    print("1. Testing get_order(123)...")
    result = get_order("123")
    print(f"   Result: {result}\n")
    
    # Test 2: Get tracking
    print("2. Testing get_tracking(123)...")
    result = get_tracking("123")
    print(f"   Result: {result}\n")
    
    # Test 3: Get Eiffel Tower info
    print("3. Testing get_eiffel_tower_info('hours')...")
    result = get_eiffel_tower_info("hours")
    print(f"   Result: {result}\n")
    
    print("4. Testing get_eiffel_tower_info('tickets')...")
    result = get_eiffel_tower_info("tickets")
    print(f"   Result: {result}\n")
    
    print("5. Testing get_eiffel_tower_info('location')...")
    result = get_eiffel_tower_info("location")
    print(f"   Result: {result}\n")


if __name__ == "__main__":
    # Test the API endpoints
    test_api_endpoints()
    
    # Print tool definitions for reference
    print("\n" + "="*80)
    print("TOOL DEFINITIONS FOR AGENT CONFIGURATION")
    print("="*80)
    print(json.dumps(TOOL_DEFINITIONS, indent=2))
