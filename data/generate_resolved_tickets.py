"""
Generates a synthetic corpus of *resolved* support tickets — each with the
resolution that fixed it. This is the knowledge base the RAG pipeline retrieves
from when drafting a suggested resolution for a new ticket (Sprint 3).

Curated (not randomly templated) so each entry pairs a realistic problem with a
concrete, useful resolution — retrieval quality depends on the corpus being
genuinely informative. No real customer data is used.

Run with: python data/generate_resolved_tickets.py
"""
import json

# (subject, body, resolution) grouped by category.
RESOLVED = {
    "billing": [
        (
            "Charged twice for my subscription",
            "I was billed twice for this month's Pro plan on the same day. Please refund the duplicate.",
            "Confirmed two identical charges caused by a retried payment after a transient gateway timeout. "
            "Refunded the duplicate charge; funds return in 5-10 business days. Added an idempotency key on "
            "renewal so a retry can no longer double-charge.",
        ),
        (
            "Refund not received after cancellation",
            "I cancelled before the renewal date but was still charged for the new month.",
            "Cancellation completed after the billing cron had already run, so the renewal went through. "
            "Issued a full refund for the unintended renewal and confirmed no future charges. Cancellations "
            "now take effect immediately and short-circuit any pending renewal for that cycle.",
        ),
        (
            "Invoice total higher than my plan price",
            "My invoice is larger than the plan price I signed up for and I don't understand the extra amount.",
            "The extra amount was prorated usage for seats added mid-cycle plus applicable tax. Walked the "
            "customer through the line items in the invoice PDF; no billing error. Suggested annual billing to "
            "reduce per-seat cost.",
        ),
        (
            "Card declined on renewal",
            "My card was declined at renewal even though I have funds. Service is now limited.",
            "The card's issuing bank flagged the recurring charge. Customer updated the card in Billing > Payment "
            "Methods and we re-ran the charge successfully, which immediately restored full access.",
        ),
        (
            "How to switch to annual billing",
            "I want to move from monthly to annual to save money. How do I do that without losing my data?",
            "Switched the plan to annual from Billing > Plan; the change prorates the unused monthly balance as a "
            "credit toward the annual term. No data is affected by a billing-interval change.",
        ),
    ],
    "product": [
        (
            "How do I export my data?",
            "I need to export all my project data to CSV but can't find the option.",
            "Export lives under Settings > Data > Export. Choose the projects and CSV format, then click Export; "
            "a download link is also emailed. Large exports are prepared in the background and can take a few minutes.",
        ),
        (
            "How to invite team members",
            "I want to add coworkers to my workspace but can't find where to invite them.",
            "Go to Settings > Members > Invite, enter each email, and pick a role (Admin/Member/Viewer). Invitees "
            "get an email link to join. Seat count updates automatically and is reflected on the next invoice.",
        ),
        (
            "Where are my projects on the free plan",
            "How many projects can I have on the free plan, and what happens if I hit the limit?",
            "The free plan allows up to 3 active projects. At the limit, new-project creation is disabled until you "
            "archive a project or upgrade. Archived projects don't count toward the limit and can be restored anytime.",
        ),
        (
            "Is there a mobile app",
            "Do you have a mobile app or is it web only? I need to check things on the go.",
            "There's no native mobile app yet, but the web app is fully responsive and works in mobile browsers. "
            "You can add it to your home screen as a PWA for an app-like experience. Logged the request for native apps.",
        ),
        (
            "How to set up notifications",
            "I'm not sure how to control which email notifications I receive.",
            "Notification preferences are under Settings > Notifications, toggled per event type (mentions, assignments, "
            "weekly digest). Changes apply immediately; check spam folder if expected emails don't arrive.",
        ),
    ],
    "account": [
        (
            "Can't reset my password",
            "The password reset email never arrives no matter how many times I request it. I'm locked out.",
            "Reset emails were landing in spam due to a strict mail filter. Whitelisted our sending domain and the "
            "email arrived. Also offered a one-time admin-issued reset link as a fallback for locked-out users.",
        ),
        (
            "Lost access to 2FA device",
            "I changed phones and can no longer get my two-factor codes, so I can't log in.",
            "Verified identity via the account's recovery email, then reset 2FA from the admin panel. Customer "
            "re-enrolled an authenticator app and saved backup codes to avoid lockout if they change devices again.",
        ),
        (
            "Change the email on my account",
            "I need to update my account email to a new work address.",
            "Updated the primary email under Settings > Account > Email; a confirmation link was sent to the new "
            "address and the change took effect once confirmed. Existing data, projects, and billing are unaffected.",
        ),
        (
            "Account locked after failed logins",
            "My account got locked after several failed login attempts. How do I get back in?",
            "Automatic lockout triggers after 5 failed attempts for security. Unlocked the account after identity "
            "verification; the lock also clears on its own after 30 minutes. Recommended a password manager to avoid repeats.",
        ),
        (
            "Removed from workspace by mistake",
            "A teammate accidentally removed me from our shared workspace and now I can't access anything.",
            "A workspace Admin re-invited the user from Settings > Members, which fully restored prior access and "
            "roles. No data was lost — removal only revokes access, it doesn't delete the member's work.",
        ),
    ],
    "bug_report": [
        (
            "App crashes on startup after update",
            "Since the latest update the app crashes instantly every time I open it.",
            "A cached client bundle from the previous version conflicted with the update. Hard refresh / clearing "
            "site data resolved it. Shipped a fix that versions cached assets so stale bundles can't cause startup crashes.",
        ),
        (
            "Export produces an empty file",
            "When I export to CSV the downloaded file is completely empty.",
            "The export was running before the report finished loading, so it captured zero rows. Fixed by disabling "
            "the export button until data is ready; as a workaround, reload the report fully, then export.",
        ),
        (
            "Dashboard stuck loading",
            "The dashboard has been stuck on a loading spinner for over an hour.",
            "A slow third-party widget was blocking the dashboard render. Disabled the widget and the dashboard "
            "loaded normally; deployed a change to load such widgets asynchronously so they can't block the page.",
        ),
        (
            "Search returns no results",
            "Search used to work but now returns nothing even for exact matches.",
            "The search index had fallen behind after a bulk import. Triggered a reindex, after which results returned "
            "correctly. Added monitoring so index lag is detected and reindexed automatically going forward.",
        ),
        (
            "Email notifications not arriving",
            "I haven't received any email notifications for days even though they're enabled.",
            "Our messages were being greylisted by the recipient's mail server. After whitelisting our domain, "
            "notifications resumed. Confirmed the user's notification settings were already enabled and correct.",
        ),
    ],
    "other": [
        (
            "Do you offer a nonprofit discount?",
            "We're a registered nonprofit — is there any discount available for organizations like us?",
            "Yes; nonprofits qualify for 30% off any paid plan. Customer emailed proof of status to support and the "
            "discount was applied to their subscription, visible on the next invoice.",
        ),
        (
            "Is my data GDPR compliant?",
            "Where is my data stored and are you GDPR compliant?",
            "Data is stored in EU-region infrastructure and processing is GDPR-compliant; shared the DPA and the "
            "privacy/security overview. Customers can request data export or deletion at any time from Settings > Data.",
        ),
        (
            "How do I cancel my account entirely?",
            "I'd like to close my account and delete all my data. What's the process?",
            "Account deletion is under Settings > Account > Delete Account; it cancels billing and permanently removes "
            "data after a 14-day grace period during which the action can be undone. Offered to export data first.",
        ),
        (
            "Partnership / integration inquiry",
            "We'd like to explore building an integration with your API. Who do we talk to?",
            "Pointed the customer to the public API docs and developer portal for keys, and routed the partnership "
            "side to the BD team, who followed up to scope the integration.",
        ),
    ],
}


def build_corpus() -> list[dict]:
    corpus = []
    next_id = 1
    for category, items in RESOLVED.items():
        for subject, body, resolution in items:
            corpus.append(
                {
                    "id": next_id,
                    "subject": subject,
                    "body": body,
                    "category": category,
                    "resolution": resolution,
                }
            )
            next_id += 1
    return corpus


def main() -> None:
    corpus = build_corpus()
    out_path = "data/resolved_tickets.json"
    with open(out_path, "w") as f:
        json.dump(corpus, f, indent=2)
    by_cat = {}
    for t in corpus:
        by_cat[t["category"]] = by_cat.get(t["category"], 0) + 1
    print(f"Wrote {len(corpus)} resolved tickets to {out_path}")
    print("By category:", by_cat)


if __name__ == "__main__":
    main()
