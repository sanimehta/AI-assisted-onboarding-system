import sys
from pathlib import Path

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent

root_agent = Agent(
    model="gemini-3.1-flash-lite",  # check AI Studio for the current Flash model name
    name="onboarding_agent",
    generate_content_config=types.GenerateContentConfig(
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2.0)
        )
    ),
instruction="""You read customer emails that request electronic document onboarding and extract the request.
Document codes: 810 = invoice, 850 = purchase order, 855 = purchase order acknowledgement (also called order confirmation), 997 = functional acknowledgement.
Fields: customer_name (string), docs (list of codes as strings), format (xml, csv, or txt; null if not stated),
ftp_owner (customer if the customer hosts the server or will provide the login details; us if the customer wants us to host it or will pull files from us; null if not stated),
questions (list of things you could not determine).
Never guess. Use null and add a question when something is not stated.
If customer_name, docs, format and ftp_owner are all known:
1. Call suggest_chain with customer_name.
2. Build a spec with keys chain, docs, format, ftp_owner, project_name
   (project_name = customer_name in lowercase with underscores instead of spaces).
3. Call check_spec. If it returns errors, fix the spec once and recheck.
4. Call preview_project only when check_spec returns no errors.
Never claim a project was created; you can only preview.
Your final answer must be ONLY a JSON object with keys customer_name, docs, format, ftp_owner, questions, preview_files (list, empty if not built). No other text.""",
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=[str(ROOT / "mcp_server.py")],
                    cwd=str(ROOT),
                ),
            ),
        )
    ],
)