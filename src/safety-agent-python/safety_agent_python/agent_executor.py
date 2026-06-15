"""
Safety Agent Executor for A2A SDK.
"""
import logging
import os

from agent_framework.foundry import FoundryChatClient
from agent_framework_a2a import A2AExecutor
from azure.identity import AzureCliCredential, ChainedTokenCredential, DefaultAzureCredential

from tools.safety_tools import evaluate_risk, is_slope_safe, get_closed_slopes

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


class SafetyAgentExecutor(A2AExecutor):

    def __init__(self):
        credential = _create_credential()
        logger.info("Safety agent using Azure credential chain (AzureCliCredential -> DefaultAzureCredential) with tenant %s", os.getenv("AZURE_TENANT_ID", "<default>"))

        agent = FoundryChatClient(project_endpoint=os.getenv("GPT41_URI"), credential=credential, model="gpt41",).as_agent(
            name="safetyagent",
            instructions="""You are the Safety Agent for AlpineAI ski resort. Your role is to evaluate risk across slopes using weather, avalanche, and visibility data. 

Safety is your top priority. Always err on the side of caution.

Risk levels:
- Low (< 0.3): Normal skiing conditions
- Moderate (0.3-0.5): Exercise caution
- High (0.5-0.7): Dangerous for some slopes
- Critical (>= 0.7): Recommend resort closure

When in doubt, recommend caution.""",
            tools=[evaluate_risk, is_slope_safe, get_closed_slopes],
        )
        super().__init__(agent, stream=True)
