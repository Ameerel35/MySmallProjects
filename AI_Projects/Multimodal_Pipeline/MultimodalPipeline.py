import os
import sys
import json
import base64
import boto3
import fitz
from typing import TypedDict, List
from PIL import Image
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings, ChatBedrockConverse
from langchain_classic.retrievers import EnsembleRetriever
from langgraph.graph import StateGraph, START, END
from ragas.metrics import context_recall, faithfulness
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.run_config import RunConfig
from datasets import Dataset
from langfuse import Langfuse
from langsmith import trace
from dotenv import load_dotenv

load_dotenv()

os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING")
os.environ["LANGSMITH_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# langfuse = Langfuse(
#     secret_key=os.getenv("LANGFUSE_SECRET"),
#     public_key=os.getenv("LANGFUSE_PUBLIC"),
#     host=os.getenv("LANGFUSE_HOST")
# )

bedrock_client = boto3.client(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    service_name=os.getenv("SERVICE_NAME"),
    region_name=os.getenv("REGION_NAME")
)
model_id_multimodal = os.getenv("model_id_multimodal")
model_id_embed = os.getenv("model_id_embed")
model_id_text = os.getenv("model_id_text")

multimodal_embeddings = BedrockEmbeddings(model_id=model_id_multimodal, client=bedrock_client)
multimodal_embeddings_two = BedrockEmbeddings(model_id=model_id_embed, client=bedrock_client)

file_name = sys.argv[1]  # Insert file here
images = []
messages = []
pages = 0
texts = []
metadatas = []
all_chunks = []

class State(TypedDict):
    results_one: list
    results_two: list
    output: str


builder = StateGraph(State)



def imageNode(state: State) -> dict[str: list]:
    paths = fitz.open(file_name)
    global pages
    pages = paths.page_count
    # Convert PDF to images
    for page_num in range(paths.page_count):
        page = paths.load_page(page_num)
        pix = page.get_pixmap()
        pix.save(f"output_page_{page_num + 1}.png")
        images.append(f"output_page_{page_num + 1}.png")

    # Encode the images
    for i, path in enumerate(images):
        with open(path, "rb") as image_file:
            encoded_file = base64.b64encode(image_file.read()).decode('utf-8')
        messages.append({"text": f"Image {i + 1}:"})
        messages.append({"image": {"format": "png", "source": {"bytes": encoded_file}}})

    messages.append({"text": "You are a document analyst. Please scan the entire image,"
                             " extract all textual information and summarize the page content"})
    paths.close()

    return {"results_one": messages}


def textNode(state: State) -> dict[str: list]:
    body = {
        "messages": [
            {
                "role": "user",
                "content": messages
            }
        ],
        "inferenceConfig": {
            "maxTokens": 200
        }
    }

    response = bedrock_client.invoke_model(
        modelId=model_id_multimodal,
        contentType='application/json',
        accept='application/json',
        body=json.dumps(body)
    )

    response_body = json.loads(response['body'].read())
    text = response_body['output']['message']['content'][0]["text"]
    metadata = {"source_url": file_name, "pages": pages}

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=0,
        length_function=len,
    )
    chunks = [
        Document(page_content=chunk, metadata=metadata)
        for chunk in text_splitter.split_text(text)
    ]
    for each_chunk in chunks:
        texts.append(each_chunk.page_content)
        metadatas.append(each_chunk.metadata)
        all_chunks.append(each_chunk)

    return {"results_two": all_chunks}

def fusionNode(state: State) -> dict[str, str]:

    vector_store = FAISS.from_texts(
        [chunk.page_content for chunk in state["results_two"]],
        embedding=multimodal_embeddings_two,
        metadatas=[c.metadata for c in state["results_two"]],
    )
    bm25_retriever = BM25Retriever.from_documents(state["results_two"], k=2)
    faiss_retriever = vector_store.as_retriever(search_kwargs={"k": 2})
    first_hybrid_retriever = EnsembleRetriever(retrievers=[bm25_retriever, faiss_retriever], weights=[0.5, 0.5])
    print("Type your query below: ")
    user_query = input()
    relevant_chunks = first_hybrid_retriever.invoke(user_query)
    if not relevant_chunks:
        print("No chunks retrieved. Prompt will be empty.")
        generated_text = "No relevant information retrieved."
        return {"output": generated_text}

    relevant_texts = ""
    for text in relevant_chunks:
        relevant_texts += text.page_content + "\n"
    relevant_prompt = f"{user_query}. Relevant information: {' '.join(relevant_texts)}. Cite relevant sources from {metadatas}."
    response = bedrock_client.converse(
        modelId=model_id_text,
        messages=[{"role": "user", "content": [{"text": relevant_prompt}]}],
        inferenceConfig={"maxTokens": 200}
    )
    content = response["output"]["message"].get("content", [])
    if not content:
        print("Bedrock returned empty content. Raw response:", response)
        return {"output": "No response generated."}

    generated_text = content[0].get("text", "")
    print(generated_text)
    hybrid_dataset = {
        "user_input": [
            "What does the color Green symbolize?",
        ],
        "retrieved_contexts": [[
            relevant_texts
        ]],
        "response": [
            generated_text
        ],
        "reference": [
            "Green wants harmony.",
        ],
    }
    # Evaluate with RAGAS (Incompatible with Python 3.13)
    # ragas_dataset = Dataset.from_dict(hybrid_dataset)
    llm = ChatBedrockConverse(client=bedrock_client, model_id=model_id_text)
    # ragas_result = evaluate(dataset=ragas_dataset, metrics=[context_recall, faithfulness],
    #                        llm=llm, embeddings=multimodal_embeddings_two)
    #
    # df = ragas_result.to_pandas()
    # logging.info(df)

    return {"output": generated_text}

builder.add_node("imageNode", imageNode)
builder.add_node("textNode", textNode)
builder.add_node("fusionNode", fusionNode)

builder.add_edge(START, "imageNode")
builder.add_edge("imageNode", "textNode")
builder.add_edge("textNode", "fusionNode")
builder.add_edge("fusionNode", END)

app = builder.compile()
result = app.invoke({"images": [], "image_messages": [], "chunks": [], "output": ""})
print("\nFinal Answer:\n", result["output"])