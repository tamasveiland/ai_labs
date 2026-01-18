# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    Given an AIProjectClient, this sample demonstrates how to use the synchronous
    `openai.evals.*` methods to create, get and list evaluation and eval runs for
    Intent Resolution evaluator with LIVE agent execution.
    
    Unlike the inline data sample, this creates an agent that runs LIVE during evaluation,
    making real tool calls and generating responses in real-time.

USAGE:
    python sample_intent_resolution_live.py

    Before running the sample:

    pip install "azure-ai-projects>=2.0.0b1" python-dotenv

    Set these environment variables with your own values:
    1) AZURE_AI_PROJECT_ENDPOINT - Required. The Azure AI Project endpoint, as found in the overview page of your
       Microsoft Foundry project. It has the form: https://<account_name>.services.ai.azure.com/api/projects/<project_name>.
    2) AZURE_AI_MODEL_DEPLOYMENT_NAME - Required. The name of the model deployment to use for evaluation.
"""

from dotenv import load_dotenv
import os
import json
import time
from pprint import pprint

import asyncio
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool
from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam,
    SourceFileContent,
    SourceFileContentContent,
)
from openai.types.eval_create_params import DataSourceConfigCustom


load_dotenv()


# Define the actual tool functions that the agent can call
def get_order(order_id: str) -> str:
    """Get the details of a specific order."""
    # Simulated order database
    orders = {
        "123": {
            "id": "123",
            "status": "shipped",
            "delivery_date": "2025-03-15",
            "items": ["Widget A", "Widget B"],
            "total": 99.99
        }
    }
    order = orders.get(order_id, {"error": "Order not found"})
    return json.dumps({"order": order})


def get_tracking(order_id: str) -> str:
    """Get tracking information for an order."""
    # Simulated tracking database
    tracking = {
        "123": {
            "tracking_number": "ABC123",
            "carrier": "UPS",
            "status": "In Transit",
            "estimated_delivery": "2025-03-15"
        }
    }
    info = tracking.get(order_id, {"error": "Tracking not found"})
    return json.dumps(info)


def get_eiffel_tower_info(info_type: str = "hours") -> str:
    """Get information about the Eiffel Tower."""
    info = {
        "hours": "Opening hours of the Eiffel Tower are 9:00 AM to 11:00 PM.",
        "tickets": "Tickets range from €10-€25 depending on access level.",
        "location": "Champ de Mars, 5 Avenue Anatole France, 75007 Paris, France"
    }
    return info.get(info_type, "Information not available")


def main() -> None:
    endpoint = os.environ[
        "AZURE_AI_PROJECT_ENDPOINT"
    ]  # Sample : https://<account_name>.services.ai.azure.com/api/projects/<project_name>
    model_deployment_name = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "")  # Sample : gpt-4o-mini

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential, api_version="2025-11-15-preview") as project_client,
        project_client.get_openai_client() as client,
    ):

        # Define tools for the agent
        # tools = ToolSet()
        
        # # Add function tools
        # get_order_tool = FunctionTool(functions=get_order)
        # get_tracking_tool = FunctionTool(functions=get_tracking)
        # get_eiffel_tower_info_tool = FunctionTool(functions=get_eiffel_tower_info)
        
        # tools.add(get_order_tool)
        # tools.add(get_tracking_tool)
        # tools.add(get_eiffel_tower_info_tool)

        # Define user functions
        user_functions = {get_order, get_tracking, get_eiffel_tower_info}
        # Initialize the FunctionTool with user-defined functions
        # functions = FunctionTool(functions=user_functions)
        # toolset = ToolSet()
        # toolset.add(functions)

        print("Creating agent with tool capabilities...")
        # Create an agent that will be evaluated
#         agent = project_client.agents.create(
#             model=model_deployment_name,
#             name="customer_service_agent",
#             instructions="""You are a friendly and helpful customer service agent.
            
# When a customer asks about order status, use the get_order tool to fetch the order details.
# When asked about tracking, use the get_tracking tool.
# When asked about the Eiffel Tower, use the get_eiffel_tower_info tool.

# Always provide clear, helpful responses that directly answer the customer's question.
# If you use tools, make sure to explain the information you found in a friendly way.""",
#             tools=functions.definitions,
#         )

        # Check if an agent with the same name exists and if not, create it
        existing_agents = list(project_client.agents.list())
        agent = next((a for a in existing_agents if a.name == "customer-service-agent-live-eval"), None)
        if agent:
            # delete existing agent to recreate
            print(f"Agent with name 'customer-service-agent-live-eval' already exists. Deleting it to recreate.")
            # project_client.agents.delete_version(agent.id, agent.version)
            # project_client.agents.delete(agent.id)
            # agent = None
        if not agent:
            # agent = project_client.agents.create(
            #     name="customer-service-agent-live-eval",
            #     definition={
            #         "kind": "prompt",
            #         "model":  {"name": model_deployment_name},
            #         "instructions": """You are a friendly and helpful customer service agent.""",
            #         "tools": functions.definitions
            #     },
            #     description="Agent for live intent resolution evaluation with tool usage.",)

            # Create an agent that will be evaluated
            agent = project_client.agents.create(
                model=model_deployment_name,
                name="customer_service_agent",
                instructions="""You are a friendly and helpful customer service agent.
                
    When a customer asks about order status, use the get_order tool to fetch the order details.
    When asked about tracking, use the get_tracking tool.
    When asked about the Eiffel Tower, use the get_eiffel_tower_info tool.

    Always provide clear, helpful responses that directly answer the customer's question.
    If you use tools, make sure to explain the information you found in a friendly way.""",
                tools=functions.definitions,
            )




            # agent = project_client.agents.create(
            #     name="customer-service-agent-live-eval",
            #     definition={
            #         "kind": "prompt",
            #         "model": {"name": model_deployment_name},
            #         "instructions": """You are a friendly and helpful customer service agent.""",
            #         "tools": functions.definitions
            #     },
            #     description="Agent for live intent resolution evaluation with tool usage.",
            # )

        print(f"✅ Agent created: {agent.id}")

        # Define evaluation schema - query and response required
        data_source_config = DataSourceConfigCustom(
            {
                "type": "custom",
                "item_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "object"}}]},
                        "response": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "object"}}]},
                        "tool_definitions": {
                            "anyOf": [{"type": "object"}, {"type": "array", "items": {"type": "object"}}]
                        },
                    },
                    "required": ["query", "response"],
                },
                "include_sample_schema": True,
            }
        )

        # Get tool definitions for the evaluator
        tool_definitions = [
            {
                "name": "get_order",
                "description": "Get the details of a specific order.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": "The order ID to get the details for."}
                    },
                    "required": ["order_id"]
                },
            },
            {
                "name": "get_tracking",
                "description": "Get tracking information for an order.",
                "parameters": {
                    "type": "object",
                    "properties": {"order_id": {"type": "string", "description": "The order ID to get tracking for."}},
                    "required": ["order_id"]
                },
            },
            {
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
                    },
                },
            },
        ]

        # Configure evaluation with agent as target
        testing_criteria = [
            {
                "type": "azure_ai_evaluator",
                "name": "intent_resolution",
                "evaluator_name": "builtin.intent_resolution",
                "initialization_parameters": {
                    "deployment_name": f"{model_deployment_name}",
                    "tool_definitions": tool_definitions  # Provide tool context to evaluator
                },
                "data_mapping": {
                    "query": "{{item.query}}",
                    "response": "{{item.response}}",  # Response from live agent execution
                    "tool_definitions": "{{item.tool_definitions}}",
                },
                "threshold": {
                    "metric": "intent_resolution",
                    "min": 4.0,
                    "aggregate": "mean"
                }
            }
        ]

        print("Creating Evaluation with live agent target...")
        # For live agent evaluation, we configure the testing criteria to use the agent
        eval_object = client.evals.create(
            name="Test Intent Resolution - Live Agent Execution",
            data_source_config=data_source_config,
            testing_criteria=testing_criteria,  # type: ignore
        )
        print(f"✅ Evaluation created: {eval_object.id}")

        # Test queries - agent will generate responses LIVE
        test_queries = [
            "What are the opening hours of the Eiffel Tower?",
            "Tell me about visiting the Eiffel Tower",
            "Hi, I need help with my order #123 status. Can you also give me tracking information?",
            "What's the status of order 123?",
        ]

        print("\n" + "="*80)
        print("RUNNING AGENT LIVE FOR EACH QUERY")
        print("="*80)
        
        # Run agent for each query and collect responses
        test_data = []

        agents_client = AgentsClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
        )
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: {query}")
            print(f"Agent id: {agent.id}")
            
            # For v2 agents, we simulate execution by calling the model with agent's instructions
            # Since v2 agents don't have a direct execution API, we use the OpenAI client
            # with the agent's model and instructions
            
            # messages = [
            #     {"role": "system", "content": agent.definition.instructions},
            #     {"role": "user", "content": query}
            # ]



            # 1) Create a conversation container (thread)
            thread = project_client.agents.create_thread()

            # 2) Add the user message
            project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=query
            )

            # 3) Run the agent against that message (handles polling + tool invocations)
            run = project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=agent.id,   # <-- pass the v2 ID as-is
            )

            if run.status == "failed":
                raise RuntimeError(f"Run failed: {run.last_error}")

            # 4) Retrieve the assistant reply
            messages = project_client.agents.list_messages(thread_id=thread.id)
            assistant_msgs = [m for m in messages if m.role == "assistant"]
            print(assistant_msgs[-1].content if assistant_msgs else "(no assistant reply)")




            messages = [
                {"role": "user", "content": query}
            ]
            # Create a new thread to run the agent
            thread_run = agents_client.create_thread_and_process_run(
                agent_id=agent.id,
                thread={ "messages": messages },
                tool_choice="auto"
            )

            # Wait for the thread to complete
            while not thread_run.is_completed:
                time.sleep(1)
                thread_run = agents_client.get_thread_run(
                    agent_id=agent.id,
                    thread_id=thread_run.thread_id,
                    run_id=thread_run.id
                )
            agent_response = thread_run.response.content
            
            
            # response = client.chat.completions.create(
            #     model=agent.definition.model.name,
            #     messages=messages,
            #     tools=functions.definitions,
            #     tool_choice="auto"
            # )
            
            # # Handle tool calls if any
            # while response.choices[0].message.tool_calls:
            #     # Add assistant response to messages
            #     messages.append(response.choices[0].message)
                
            #     # Execute each tool call
            #     for tool_call in response.choices[0].message.tool_calls:
            #         function_name = tool_call.function.name
            #         function_args = json.loads(tool_call.function.arguments)
                    
            #         # Call the actual function
            #         if function_name == "get_order":
            #             function_response = get_order(**function_args)
            #         elif function_name == "get_tracking":
            #             function_response = get_tracking(**function_args)
            #         elif function_name == "get_eiffel_tower_info":
            #             function_response = get_eiffel_tower_info(**function_args)
            #         else:
            #             function_response = json.dumps({"error": "Unknown function"})
                    
            #         # Add tool response to messages
            #         messages.append({
            #             "role": "tool",
            #             "tool_call_id": tool_call.id,
            #             "content": function_response
            #         })
                
            #     # Get next response from model
            #     response = client.chat.completions.create(
            #         model=agent.definition.model.name,
            #         messages=messages,
            #         tools=functions.definitions,
            #         tool_choice="auto"
            #     )
            
            # # Extract the final agent response
            # agent_response = response.choices[0].message.content
            
            print(f"   Response: {agent_response}")
            
            # Store for evaluation
            test_data.append({
                "query": query,
                "response": agent_response,
                "tool_definitions": tool_definitions
            })
        
        print("="*80 + "\n")

        print("Creating Eval Run with live agent responses...")
        eval_run_object = client.evals.runs.create(
            eval_id=eval_object.id,
            name="live_agent_run",
            metadata={"team": "eval-exp", "scenario": "live-agent-v1"},
            data_source=CreateEvalJSONLRunDataSourceParam(
                type="jsonl",
                source=SourceFileContent(
                    type="file_content",
                    content=[
                        SourceFileContentContent(item=item)
                        for item in test_data
                    ],
                ),
            ),
        )

        print(f"✅ Eval Run created: {eval_run_object.id}")
        print("🔄 Agent is now running live for each test query...")
        pprint(eval_run_object)

        print("\n\n----Waiting for Live Eval Run to Complete----\n")

        while True:
            run = client.evals.runs.retrieve(run_id=eval_run_object.id, eval_id=eval_object.id)
            print(f"Status: {run.status}")
            
            if run.status == "completed" or run.status == "failed":
                print("\n" + "="*80)
                print("EVALUATION RESULTS")
                print("="*80)
                
                output_items = list(client.evals.runs.output_items.list(run_id=run.id, eval_id=eval_object.id))
                
                for i, item in enumerate(output_items, 1):
                    print(f"\n--- Test Case {i} ---")
                    if hasattr(item, 'input') and item.input:
                        print(f"Query: {item.input.get('query', 'N/A')}")
                    if hasattr(item, 'output') and item.output:
                        print(f"Agent Response: {item.output.get('response', 'N/A')[:200]}...")
                    if hasattr(item, 'scores'):
                        print(f"Intent Resolution Score: {item.scores}")
                    print()
                
                print(f"✅ Eval Run Status: {run.status}")
                print(f"📊 Eval Run Report URL: {run.report_url}")
                print("="*80)
                break
                
            time.sleep(5)
            print("⏳ Waiting for eval run to complete...")

        # Cleanup
        print(f"\n🧹 Cleaning up agent: {agent.id}")
        project_client.agents.delete_agent(agent.id)
        print("✅ Agent deleted")


if __name__ == "__main__":
    main()
