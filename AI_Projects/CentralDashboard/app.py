import pandas as pd
import streamlit as st
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import uvicorn
from pathlib import Path

data_source = Path("agentic_metrics.csv")

def load_csv():
    if not data_source.exists():
        return pd.DataFrame(columns=[
            "Timestamp", "Cloudwatch Metric", "Value",
            "Unit", "Agent", "Tenant", "Bedrock LLM model_id", "Langfuse trace_id", "Total tokens used"
        ])
    return pd.read_csv(data_source)

def save_csv(df):
    df.to_csv(data_source, index=False)

df = load_csv()

api = FastAPI(title="Central Dashboard")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/tenants/{Tenant}/users")
def get_users(Tenant: str):
    return df[df["Tenant"] == Tenant].to_dict(orient="records")

@api.post("/reload")
def reload_data():
    global df
    df = load_csv()
    return {"status": "reloaded"}

if "df" not in st.session_state:
    st.session_state.df = load_csv()

def streamlit_app():
    st.title("Central Dashboard")

    df = st.session_state.df

    Tenant = st.selectbox(
        "Select Tenant",
        sorted(df["Tenant"].unique())
    )

    # tenant_df = df[df["Tenant"] == Tenant]

    #st.subheader("Users")
    st.dataframe(df[df["Tenant"] == Tenant])

    if st.button("Reload CSV"):
        st.session_state.df = load_csv()
        df = load_csv()
        st.success("CSV Reloaded")

def run_api():
    uvicorn.run(api, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    threading.Thread(target=run_api, daemon=True).start()
    streamlit_app()
