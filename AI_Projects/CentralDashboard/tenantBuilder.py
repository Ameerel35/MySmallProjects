import os
import boto3
import sys
import json
import langsmith
from tenacity import retry, stop_after_attempt, wait_fixed
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()

class Tenant:
    def __init__(self, role):
        self.role = role

class State(TypedDict):
    trace_id: str
    tenant: str
    response: str
    latency_ms: float
    decision: str