from google.adk.agents.llm_agent import Agent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import google_search
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
import os
# import asyncio
# import datetime
# import requests
# from google.adk.runners import InMemoryRunner
# from google.genai import types
import random

GEMINI_MODEL="gemini-2.5-flash"
TARGET_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C:/Users/Admin/OneDrive - Cardiff University/Documents")

def get_team() -> str:
    """Returns a randomly selected F1 team."""
    sample = ["Mercedes", "Ferrari", "Red Bull"]
    team = random.choice(sample)
    return team


def get_role(team: str) -> dict:
    """Returns a role recommendation for the given team."""
    
    roles = {
        "Mercedes": "Lead Driver",
        "Ferrari": "Technical Driver",
        "Red Bull": "Performance Driver"
    }

    return {
        "role": roles.get(team, "Reserve Driver")
    }


def get_report(team: str, role: str) -> dict:
    """Produces a summary report of your recommended team and role."""
    
    report = f"""
    🏁 F1 Recommendation Report
    ----------------------------
    Recommended Team: {team}
    Assigned Role: {role}
    
    This combination maximizes competitive potential and strategic advantage.
    """

    return {
        "status": "success",
        "report": report.strip()
    }

# A single step agent
# root_agent = Agent(
#     model=GEMINI_MODEL,
#     name="root_agent",
#     description="A helpful assistant for F1 team questions.",
#     instruction="""
# Recommend a team for the user based on preferences.""",
#     tools=[google_search],
# )

# PARALLEL execution
# sub_agent_1 = LlmAgent(
#      name="TeamDescription",
#      model=GEMINI_MODEL,
#      instruction="""
#      You are an AI F1 Expert System.
#      Describe one team you have found in 1 sentence.
#      """,
#      description="Describes a F1 Team.",
#      tools=[google_search],
#      # Store result in state for the merger agent
#      output_key="team_result"
#  )

# sub_agent_2 = LlmAgent(
#      name="RoleDescription",
#      model=GEMINI_MODEL,
#      instruction="""
#      You are an AI F1 Expert System.
#      Describe a role you have found in a team in 1 sentence.
#      """,
#      description="Describes an F1 Role.",
#      tools=[google_search],
#      # Store result in state for the merger agent
#      output_key="role_result"
#  )

# parallel_sub_agent = ParallelAgent(
#      name="ParallelRecommendationAgent",
#      sub_agents=[sub_agent_1, sub_agent_2],
#      description="Runs multiple research agents in parallel to gather recommendations."
#  )

# root_agent = parallel_sub_agent

# SEQUENTIAL agent execution
# root_agent = Agent(
#     model="gemini-2.5-flash",
#     name="root_agent",
#     description="A helpful assistant for F1 team questions.",
#     instruction="""
# You must use tools in this exact order:

# 1. Call get_team
# 2. Use the returned team to call get_role
# 3. Use both outputs to call get_report
# 4. Return ONLY the final report to the user

# Do not skip tools.
# Do not answer manually.
# """,
#     tools=[get_team, get_role, get_report],
# )

# MCP Experiment
root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='filesystem_assistant_agent',
    instruction='Help the user manage their files. You can list files, read files, etc.',
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params = StdioServerParameters(
                    command='npx',
                    args=[
                        "-y",
                        "@modelcontextprotocol/server-filesystem",
                        os.path.abspath(TARGET_FOLDER_PATH),
                    ],
                ),
            ),
            # Optional: Filter which tools from the MCP server are exposed
            # tool_filter=['list_directory', 'read_file']
        )
    ],
)