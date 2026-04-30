Application Title: Multimodal RAG Assistant

Overview: This application allows you to load multimodal PDF files to be processed for RAG (Retrieval Augmentation Generation), leading to a desired response in your queries.

Files required:
- MultimodalPipeline.py Python file
- A PDF Document for Testing inputted via CLI (Document could include an image)

Technologies required:
- Python Programming Language
- Langchain/Langgraph Framework
- Langsmith Tracing
- Amazon Bedrock LLM & Embeddings
- FAISS Library
- BM25 Index
- RAGAS Evaluation Metrics

RAGAS Evaluation Schema:
user_input : String (The query of the user)
retrieved_contexts : List (The relevant chunks of text from the PDF document)
Response : String (The response provided by the LLM)
Reference : String (The standard response for metric measurement)

Step-by-Step Walkthrough:
1. Load the MultimodalPipeline python file using any CLI (thought Command Prompt is preferred) and include the name of the file you want to load into the Vector database as a CLI parameter.
2. The application will pre-process the document as images to be encoded and analyzed by a LLM.
3. Next, the summarized analysis will be chunked and embedded into the vector databases before being retrieved by the hybrid retriever.
4. You will then be prompted to input a query to test if the Q&A program can respond correctly using a LLM (Amazon Bedrock) and the Vector database.
5. A response will be provided.
6. RAGAS will evaluate the performance of the selected retrieval strategy.
7. The application will terminate. Repeat the application processes with a new filename in the CLI if desired.

Extra important notes
- The API keys were inputted from a .env file for confidentiality. Please make your own .env file to match the 'os.environ' setups, such as your own LangSmith API key and Amazon Web Services keys, if you would like to test the application on your own device.
- The PDF file used for testing is "MultiMTGColorResults.pdf", which explains the context of the colors.