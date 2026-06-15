"""
Ski Coach Agent Executor for A2A SDK.
"""
import logging
import os

from agent_framework.foundry import FoundryChatClient
from agent_framework_a2a import A2AExecutor
from azure.identity import AzureCliCredential, ChainedTokenCredential, DefaultAzureCredential

from tools.coach_tools import recommend_slope, build_day_plan

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


class SkiCoachAgentExecutor(A2AExecutor):

    def __init__(self):
        credential = _create_credential()
        logger.info("Ski coach agent using Azure credential chain (AzureCliCredential -> DefaultAzureCredential) with tenant %s", os.getenv("AZURE_TENANT_ID", "<default>"))

        agent = FoundryChatClient(project_endpoint=os.getenv("GPT41_URI"), credential=credential, model="gpt41").as_agent(
            name="skicoachagent",
            instructions="""You are the Ski Coach Agent for AlpineAI ski resort. You help skiers find the best slopes based on their skill level, preferences, and current conditions.

When users ask for recommendations, always ask about their skill level if not provided (beginner, intermediate, advanced, expert).
Use the recommend_slope tool to get current conditions and recommendations.
Use the build_day_plan tool to create a structured day schedule.

Always be encouraging and helpful. Skiing should be fun and safe!""",
            tools=[recommend_slope, build_day_plan],
        )
        super().__init__(agent, stream=True)
