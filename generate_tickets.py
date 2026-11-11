import json
import random
from datetime import date, timedelta
from pathlib import Path


CATEGORIES = ["billing", "login", "bug", "feature request"]
STATUSES = ["open", "closed"]

TITLES = {
    "billing": ["Unexpected charge on invoice", "Question about my subscription", "Request for a refund"],
    "login": ["Unable to sign in", "Password reset link not working", "Account locked after login attempts"],
    "bug": ["Page freezes when I save", "Search results are not loading", "Settings do not stay updated"],
    "feature request": ["Add dark mode", "Allow exporting reports", "Support additional language"],
}

DESCRIPTIONS = {
    "billing": ["The latest invoice includes a charge I do not recognize.", "Please help me understand the amount on my recent bill.", "I would like help reviewing a payment on my account."],
    "login": ["I cannot access my account with my usual credentials.", "The sign-in process stops before opening my account.", "I need help getting back into my account."],
    "bug": ["This behavior happens each time I try the same action.", "The page does not behave as expected on my device.", "I noticed this issue while using the latest version."],
    "feature request": ["This option would make my regular workflow easier.", "It would be helpful to have this choice in the product.", "Please consider adding this capability in a future update."],
}


def main():
    today = date.today()
    tickets = []

    for ticket_number in range(1, 51):
        category = random.choice(CATEGORIES)
        created = today - timedelta(days=random.randint(0, 59))
        tickets.append(
            {
                "id": f"TKT-{ticket_number:04d}",
                "title": random.choice(TITLES[category]),
                "category": category,
                "status": random.choice(STATUSES),
                "created_at": created.isoformat(),
                "description": random.choice(DESCRIPTIONS[category]),
            }
        )

    output_path = Path(__file__).with_name("tickets.json")
    output_path.write_text(json.dumps(tickets, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
