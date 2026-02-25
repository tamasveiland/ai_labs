# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

#
# Taken from https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/samples/responses/sample_responses_basic_async.py
#

"""
DESCRIPTION:
    This sample demonstrates how to run a basic responses operation
    using the asynchronous AIProjectClient and AsyncOpenAI clients.

    See also https://platform.openai.com/docs/api-reference/responses/create?lang=python

USAGE:
    python sample_responses_basic_async.py

    Before running the sample:

    pip install "azure-ai-projects>=2.0.0b4" python-dotenv aiohttp

    Set these environment variables with your own values:
    1) AZURE_AI_PROJECT_ENDPOINT - The Azure AI Project endpoint, as found in the Overview
       page of your Microsoft Foundry portal.
    2) AZURE_AI_MODEL_DEPLOYMENT_NAME - The deployment name of the AI model, as found under the "Name" column in
       the "Models + endpoints" tab in your Microsoft Foundry project.
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.identity.aio import ClientSecretCredential
from azure.ai.projects.aio import AIProjectClient

load_dotenv()

endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]


async def main() -> None:

    async with (
        ClientSecretCredential(
            tenant_id=os.environ.get("AZURE_TENANT_ID"),
            client_id=os.environ.get("AZURE_CLIENT_ID"),
            client_secret=os.environ.get("AZURE_CLIENT_SECRET")
        ) as credential,
        AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):
        response = await openai_client.responses.create(
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            input="What is the size of France in square miles?",
        )
        print(f"Response output: {response.output_text}")

        response = await openai_client.responses.create(
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            input="And what is the capital city?",
            previous_response_id=response.id,
        )
        print(f"Response output: {response.output_text}")


if __name__ == "__main__":
    asyncio.run(main())