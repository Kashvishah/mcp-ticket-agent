import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import Client, StdioServerParameters
from openai import AsyncOpenAI

SERVER_DIR = Path(__file__).resolve().parent
load_dotenv(SERVER_DIR / ".env")
MODEL = os.getenv("OPENAI_MODEL", "gpt-6-astra")
INSTRUCTIONS = "Use ticket tools for facts; do not guess. Explain results in plain words."


def _server_parameters():
    return StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_DIR / "server.py")],
        cwd=str(SERVER_DIR),
    )


def _tool_definitions(listed):
    tools = [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
            "strict": False,
        }
        for tool in listed.tools
    ]
    return tools, {tool.name for tool in listed.tools}


def _result_payload(result):
    value = result.structured_content
    if value is None:
        value = [block.model_dump(mode="json") for block in result.content]
    return {"is_error": result.is_error, "result": value}


async def _continue_response(llm, mcp, response, tools, known_tools):
    for _ in range(8):
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return {"answer": response.output_text or "I couldn't produce a text answer."}

        call = calls[0]  # parallel_tool_calls=False keeps the confirmation flow one action at a time.
        arguments = json.loads(call.arguments)
        if call.name == "create_ticket":
            return {
                "pending": {
                    "response_id": response.id,
                    "call_id": call.call_id,
                    "arguments": arguments,
                }
            }
        if call.name in known_tools:
            result = await mcp.call_tool(call.name, arguments)
            payload = _result_payload(result)
        else:
            payload = {"error": f"Unknown tool: {call.name}"}

        response = await llm.responses.create(
            model=MODEL,
            instructions=INSTRUCTIONS,
            tools=tools,
            parallel_tool_calls=False,
            previous_response_id=response.id,
            input=[
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(payload, ensure_ascii=False),
                }
            ],
        )
    return {"answer": "I stopped after too many tool calls. Please try a simpler question."}


async def ask_agent(question: str, history: list[dict] | None = None) -> dict:
    """Ask the MCP ticket server; return an answer or a pending ticket for confirmation."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Add OPENAI_API_KEY to the .env file before starting the agent.")

    async with AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"]) as llm:
        async with Client(_server_parameters()) as mcp:
            tools, known_tools = _tool_definitions(await mcp.list_tools())
            response = await llm.responses.create(
                model=MODEL,
                instructions=INSTRUCTIONS,
                tools=tools,
                parallel_tool_calls=False,
                input=[*(history or []), {"role": "user", "content": question}],
            )
            return await _continue_response(llm, mcp, response, tools, known_tools)


async def confirm_create_ticket(pending: dict, confirm: bool = True) -> dict:
    """Run a proposed create_ticket call only after the user confirms it."""
    if not confirm:
        return {"answer": "Ticket creation cancelled; nothing was saved."}
    async with AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"]) as llm:
        async with Client(_server_parameters()) as mcp:
            tools, known_tools = _tool_definitions(await mcp.list_tools())
            result = await mcp.call_tool("create_ticket", pending["arguments"])
            response = await llm.responses.create(
                model=MODEL,
                instructions=INSTRUCTIONS,
                tools=tools,
                parallel_tool_calls=False,
                previous_response_id=pending["response_id"],
                input=[
                    {
                        "type": "function_call_output",
                        "call_id": pending["call_id"],
                        "output": json.dumps(_result_payload(result), ensure_ascii=False),
                    }
                ],
            )
            return await _continue_response(llm, mcp, response, tools, known_tools)


async def main():
    history = []
    while True:
        question = input("You (or 'quit'): ").strip()
        if question.casefold() in {"quit", "exit"}:
            break
        result = await ask_agent(question, history)
        while "pending" in result:
            ticket = result["pending"]["arguments"]
            print(f"Proposed ticket: {ticket}\n")
            answer = input("Save this ticket? [y/N]: ").strip().casefold()
            result = await confirm_create_ticket(result["pending"], answer == "y")
        answer = result["answer"]
        print(f"Agent: {answer}\n")
        history.extend([{"role": "user", "content": question}, {"role": "assistant", "content": answer}])


if __name__ == "__main__":
    asyncio.run(main())
