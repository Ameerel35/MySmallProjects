import tenantBuilder
import boto3, os, sys
import time
import uuid
import csv
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
# from redactor import Redactor
from langfuse import Langfuse, get_client, observe 
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
load_dotenv()

csv_file = "agentic_metrics.csv"

bedrock_client = boto3.client(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    service_name=os.getenv("SERVICE_NAME"),
    region_name=os.getenv("REGION_NAME")
)
cloudwatch = boto3.client("cloudwatch", region_name=os.getenv("REGION_NAME"))
langfuse = Langfuse(public_key=os.getenv("LANGFUSE_PUBLIC_KEY"), secret_key=os.getenv("LANGFUSE_SECRET_KEY"), host="https://cloud.langfuse.com")
tenant = tenantBuilder.Tenant("Food")
# redactor = Redactor()

class State(TypedDict):
    trace_id: str
    tenant: str
    response: str
    latency_ms: float
    flow_count: int

recipe = sys.argv[1]

prompt = f"""You are a {tenant.role} specialist. Inspect the recipe from {recipe} and provide a quick summary 
            on how to prepare the dish. State your role as well and cite APIs used."""

def write_metric_to_csv(metric_name, value, unit, dimensions, trace_id, total_tokens):
    file_exists = os.path.exists(csv_file)

    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "Timestamp",
                "Cloudwatch Metric",
                "Value",
                "Unit",
                "Agent",
                "Tenant",
                "Bedrock LLM model_id",
                "Langfuse trace_id",
                "Total tokens used"
            ])

        writer.writerow([
            datetime.utcnow().isoformat(),
            metric_name,
            value,
            unit,
            dimensions.get("Agent"),
            dimensions.get("Tenant"),
            dimensions.get("ModelId"),
            trace_id,
            total_tokens
        ])

def publish_bedrock_metrics(
    agent_name: str,
    tenant: str,
    model_id: str,
    latency_ms: float,
    total_tokens: int,
    trace_id: str # Extra dimension
):
    
    dimensions = {
        "Agent": agent_name,
        "Tenant": tenant,
        "ModelId": model_id
    }

    cloudwatch.put_metric_data(
        Namespace="AgenticAI/Bedrock",
        MetricData=[
            {
                "MetricName": "BedrockInvocationLatency",
                "Dimensions": [
                    {"Name": n, "Value": v} for n, v in dimensions.items()
                ],
                "Value": latency_ms,
                "Unit": "Milliseconds"
            },
            {
                "MetricName": "BedrockInvocations",
                "Dimensions": [
                    {"Name": "Agent", "Value": agent_name}
                ],
                "Value": 1,
                "Unit": "Count"
            }
        ]
    )

    write_metric_to_csv(
        metric_name="BedrockInvocationLatency",
        value=latency_ms,
        unit="Milliseconds",
        dimensions=dimensions,
        trace_id=trace_id,
        total_tokens=total_tokens
    )

    write_metric_to_csv(
        metric_name="BedrockInvocations",
        value=1,
        unit="Count",
        dimensions=dimensions,
        trace_id=trace_id,
        total_tokens=total_tokens
    )

@observe(name="reporter_agent")
def reporter_agent(state: State) -> State:

    trace_id = str(uuid.uuid4())
    state["trace_id"] = trace_id

    langfuse.update_current_trace(
        metadata={
            "tenant": state["tenant"],
            "agent": "reporter_agent",
            "model": os.getenv("model_id_text"),
            "trace_id": trace_id,
            "bedrock_invocations": 1
            # "bedrock_latency_ms": state["latency_ms"],          
        }
    )

    start_time = time.time()

    response = bedrock_client.converse(
        modelId=os.getenv("model_id_text"),
        messages=[{
            "role": "user",
            "content": [{"text": prompt}]
        }],
        inferenceConfig={"maxTokens": 100}
    )

    latency_ms = (time.time() - start_time) * 1000
    output_text = response["output"]["message"]["content"][0]["text"]

    # redacted_text, mappings = redactor.redact(output_text)

    usage = response.get("usage", {})

    input_tokens = usage.get("inputTokens", 0)
    output_tokens = usage.get("outputTokens", 0)
    total_tokens = usage.get("totalTokens", input_tokens + output_tokens)

    state["response"] = output_text
    state["latency_ms"] = latency_ms

    publish_bedrock_metrics(
        agent_name="reporter_agent",
        tenant=state["tenant"],
        model_id=os.getenv("model_id_text"),
        latency_ms=latency_ms,
        trace_id=trace_id,
        total_tokens=total_tokens
    )

    return state

def end_node(state: State) -> State:
    state["flow_count"] += 1
    return state

builder = StateGraph(State)
builder.add_node("reporter", reporter_agent)
builder.add_node("endpoint", end_node)
builder.add_edge(START, "reporter")
builder.add_edge("reporter", "endpoint")
builder.add_edge("endpoint", END)
app = builder.compile()
result = app.invoke({"trace_id": "", "tenant": tenant.role, "response": "", "latency_ms": 0, "flow_count": 0})
print(result)
