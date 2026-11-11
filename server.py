import json
from datetime import date
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("Ticket Agent")
except ModuleNotFoundError:
    from mcp.server import MCPServer

    mcp = MCPServer("Ticket Agent")

TICKETS_FILE = Path(__file__).with_name("tickets.json")
with TICKETS_FILE.open(encoding="utf-8") as file:
    TICKETS = json.load(file)

CATEGORIES = ["billing", "login", "bug", "feature request"]


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """Find one support ticket by its ID."""
    for ticket in TICKETS:
        if ticket["id"].casefold() == ticket_id.casefold():
            return ticket
    return {"error": f"No ticket found with ID {ticket_id}."}


@mcp.tool()
def search_tickets(keyword: str) -> list[dict]:
    """Find support tickets whose title or description contains a keyword."""
    keyword = keyword.casefold()
    return [
        ticket
        for ticket in TICKETS
        if keyword in ticket["title"].casefold()
        or keyword in ticket["description"].casefold()
    ]


@mcp.tool()
def count_by_category() -> dict[str, int]:
    """Count all tickets in each category."""
    counts = {category: 0 for category in CATEGORIES}
    for ticket in TICKETS:
        counts[ticket["category"]] += 1
    return counts


@mcp.tool()
def tickets_open_longer_than(days: int) -> list[dict]:
    """List open tickets created more than the given number of days ago."""
    if days < 0:
        raise ValueError("days must be zero or greater.")

    today = date.today()
    return [
        ticket
        for ticket in TICKETS
        if ticket["status"] == "open"
        and (today - date.fromisoformat(ticket["created_at"])).days > days
    ]


@mcp.tool()
def create_ticket(title: str, category: str, description: str) -> dict:
    """Create and save a new open support ticket."""
    if category not in CATEGORIES:
        raise ValueError(f"category must be one of: {', '.join(CATEGORIES)}.")

    next_number = max(
        (int(ticket["id"].removeprefix("TKT-")) for ticket in TICKETS),
        default=0,
    ) + 1
    ticket = {
        "id": f"TKT-{next_number:04d}",
        "title": title,
        "category": category,
        "status": "open",
        "created_at": date.today().isoformat(),
        "description": description,
    }

    updated_tickets = [*TICKETS, ticket]
    TICKETS_FILE.write_text(
        json.dumps(updated_tickets, indent=2) + "\n", encoding="utf-8"
    )
    TICKETS.append(ticket)
    return ticket


if __name__ == "__main__":
    mcp.run()
