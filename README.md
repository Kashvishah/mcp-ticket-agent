# Ticket Agent

## What it is

Ticket Agent is a small chat app for creating and searching fictional support tickets. It uses an OpenAI LLM and an MCP server, with ticket data stored in `tickets.json`.

## How it works

1. You ask a question in the Streamlit chat.
2. `agent.py` sends your question and the available tools to the LLM.
3. The LLM picks a tool and its inputs; ticket creation waits for your confirmation.
4. The MCP server reads or updates `tickets.json` and returns the result to the chat.

## Run it

From the project’s parent folder:

```bash
cd ticket-agent
python3 -m venv .venv
source .venv/bin/activate
pip install "mcp[cli]" openai streamlit
```

Add your OpenAI key to `.env`:

```text
OPENAI_API_KEY=your_key_here
```

Then start the chat app:

```bash
python -m streamlit run app.py
```

Ticket data in this project is fictional. Before `create_ticket` saves a ticket, the app shows its details and asks you to confirm.
