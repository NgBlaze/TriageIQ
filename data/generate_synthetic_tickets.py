"""
Generates a synthetic dataset of customer support tickets for development
and testing. No real customer data is used anywhere in this project.

Run with: python data/generate_synthetic_tickets.py
"""
import json
import random

random.seed(42)

TEMPLATES = {
    "billing": [
        ("Duplicate charge on my account", "I was charged twice for my subscription this month. Please refund one of the charges."),
        ("Question about invoice", "Can you explain why my invoice total is higher than my usual plan price?"),
        ("Need a refund", "I cancelled my subscription last week but was still charged. I'd like a refund."),
        ("Payment method declined", "My card was declined during renewal but I have funds available. Can you check what happened?"),
        ("Upgrade pricing question", "What would it cost to upgrade from the Basic to the Pro plan mid-cycle?"),
    ],
    "product": [
        ("How do I export my data?", "I can't find the export option anywhere in the settings menu. Where is it located?"),
        ("Feature request: dark mode", "It would be great if the app supported a dark theme for night-time use."),
        ("How to invite team members", "I want to add three coworkers to my workspace but can't find an invite option."),
        ("Is there a mobile app?", "Does your product have a mobile app, or is it web-only?"),
        ("Question about plan limits", "How many projects can I create on the free plan before needing to upgrade?"),
    ],
    "account": [
        ("Can't reset my password", "The password reset email never arrives even after multiple attempts. I'm locked out."),
        ("Two-factor authentication issue", "I lost access to my old phone number and can't get my 2FA codes anymore."),
        ("Need to change my email", "I want to update the email address associated with my account."),
        ("Account locked after failed logins", "My account got locked after a few failed login attempts. How do I unlock it?"),
        ("Can't access team workspace", "I was removed from my team's workspace by mistake and need access restored."),
    ],
    "bug_report": [
        ("App crashes on startup", "Since the latest update, the app crashes immediately every time I open it."),
        ("Export feature produces empty file", "When I export my report to CSV, the downloaded file is completely empty."),
        ("Dashboard not loading", "The main dashboard has been stuck on a loading spinner for the past hour."),
        ("Search returns no results", "Search used to work fine but now returns zero results even for exact matches."),
        ("Notifications not arriving", "I haven't received any email notifications in the past three days despite having them enabled."),
    ],
    "other": [
        ("General feedback", "Just wanted to say the new UI redesign looks great, nice work!"),
        ("Partnership inquiry", "We're interested in exploring an integration partnership, who should I talk to?"),
        ("Question about your roadmap", "Is there a public roadmap I can check to see upcoming features?"),
        ("Press inquiry", "I'm writing an article about productivity tools and would like a quick comment from your team."),
        ("Compliment", "Your support team helped me last week and they were fantastic, just wanted to say thanks."),
    ],
}

PRIORITY_HINTS = {
    "critical": ["", " This is affecting our entire team and we cannot work.", " This is urgent, please help immediately."],
    "high": ["", " This is blocking important work for me.", " I need this resolved soon."],
    "medium": ["", " Not urgent but I'd appreciate a resolution soon.", ""],
    "low": ["", " No rush, just flagging it.", ""],
}

# Rough priority distribution per category (category, priority weighting reflects realistic patterns)
PRIORITY_WEIGHTS = {
    "billing": {"critical": 0.05, "high": 0.25, "medium": 0.5, "low": 0.2},
    "product": {"critical": 0.02, "high": 0.13, "medium": 0.35, "low": 0.5},
    "account": {"critical": 0.1, "high": 0.4, "medium": 0.35, "low": 0.15},
    "bug_report": {"critical": 0.25, "high": 0.35, "medium": 0.3, "low": 0.1},
    "other": {"critical": 0.0, "high": 0.05, "medium": 0.25, "low": 0.7},
}


def weighted_choice(weights: dict) -> str:
    items, probs = zip(*weights.items())
    return random.choices(items, weights=probs, k=1)[0]


def generate_tickets(n: int) -> list[dict]:
    tickets = []
    categories = list(TEMPLATES.keys())

    for i in range(n):
        category = random.choice(categories)
        subject, body = random.choice(TEMPLATES[category])
        priority = weighted_choice(PRIORITY_WEIGHTS[category])
        hint = random.choice(PRIORITY_HINTS[priority])

        tickets.append({
            "id": i + 1,
            "subject": subject,
            "body": body + hint,
            "true_category": category,
            "true_priority": priority,
        })

    return tickets


if __name__ == "__main__":
    dataset = generate_tickets(200)

    with open("data/synthetic_tickets.json", "w") as f:
        json.dump(dataset, f, indent=2)

    # Carve out a smaller labeled eval subset for classifier accuracy testing
    eval_set = random.sample(dataset, 50)
    with open("data/eval_set.json", "w") as f:
        json.dump(eval_set, f, indent=2)

    print(f"Generated {len(dataset)} synthetic tickets -> data/synthetic_tickets.json")
    print(f"Carved out {len(eval_set)} tickets for evaluation -> data/eval_set.json")
