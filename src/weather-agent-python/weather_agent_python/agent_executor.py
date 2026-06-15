"""
Weather Agent Executor for A2A SDK.
"""
import logging
import os

from agent_framework.foundry import FoundryChatClient
from agent_framework_a2a import A2AExecutor
from azure.identity import AzureCliCredential, ChainedTokenCredential, DefaultAzureCredential

from tools.weather_tools import get_current_conditions, get_forecast, is_storm_incoming

logger = logging.getLogger(__name__)


def _create_credential():
    tenant_id = os.getenv("AZURE_TENANT_ID")

    cli_credential = AzureCliCredential(tenant_id=tenant_id) if tenant_id else AzureCliCredential()

    # Keep a non-MI fallback for local reliability (avoids IMDS latency/noise on dev machines).
    fallback_credential = DefaultAzureCredential(
        exclude_managed_identity_credential=True,
        exclude_interactive_browser_credential=True,
    )

    return ChainedTokenCredential(cli_credential, fallback_credential)


class WeatherAgentExecutor(A2AExecutor):

    def __init__(self):
        credential = _create_credential()
        logger.info("Weather agent using Azure credential chain (AzureCliCredential -> DefaultAzureCredential) with tenant %s", os.getenv("AZURE_TENANT_ID", "<default>"))

        agent = FoundryChatClient(project_endpoint=os.getenv("GPT41_URI"), credential=credential, model="gpt41").as_agent(
            name="weatheragent",
            instructions="""You are the Weather Intelligence Agent for AlpineAI ski resort. 
Your role is to help skiers, staff, and resort operators understand current weather conditions, 
upcoming forecasts, and potential storm threats.

When users ask questions, always provide specific numbers and actionable recommendations.
Be concise but thorough. Safety is the top priority.""",
            tools=[get_current_conditions, get_forecast, is_storm_incoming],
        )
        super().__init__(agent, stream=True)
