Application Title: Agentic Workflow Orchestra

Overview: This application allows you to run multiple client ( tenant) files for Agentic AI workflows, and record the metrics of the usage onto a centralised csv file,
which can then be uploaded and visualised on a table dashboard on Grafana cloud.

Files required:
- A csv file (Will be created in same directory as Python tenant file)
- At least one instance of a Python tenant filel.

Technologies required:
- Python Programming Language
- Langchain Framework
- Langgraph for the Agents
- Microsoft Excel
- Any LLM (Amazon Bedrock is recommended)
- Grafana Cloud account

Step-by-Step Walkthrough:
1. Load any Python file that has the word 'Tenant'. It is intended to demonstrate an Agentic workflow isolated from the other tenants.
2. The program requires a file to be uploaded, preferably a food-related document or game-related document as the existing tenants act as either a food or game assistant.
3. The reporter agent in the codebase will go through the documents and provide a visible response to the user.
4. Throughout this procedure, metrics to indicate which technologies were utilized such as Cloudwatch and Langfuse would be captured and stored on a csv file.
5. The csv file is then to be uploaded to a singular dashboard.

Extra important notes
- The API keys were from a .env file.
- A singular csv file was intended to be the central data source for the unified dashboard of multi-tenancy workflow reports. By running more than one tenants, more data would be captured and stored on the csv file.
- The tenantBuilder.py file is intended to be a pattern containing classes which other files can replicate to provide a consistent model of the data and metrics required.