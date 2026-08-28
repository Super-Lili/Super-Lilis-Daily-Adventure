"""Invoice Follow-Up Sequencer.

Requirements: python-dateutil (optional), standard library otherwise.
"""
import math
import re
import sys
from datetime import date, datetime, timedelta

try:
    from dateutil import parser as dateparser
except ImportError:
    dateparser = None

FIELDS = ["Outlet", "Portal", "Contact", "Email", "Invoice", "Amount",
          "Issued", "TermsDays", "LastFollowup", "FollowupCount", "LastResponse"]
DEFAULTS = ["Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "0",
            "Unknown", "30", "Unknown", "0", "Unknown"]
REFERENCE_LINE = "Reference example: invoice INV-0391 for $1,250 is Escalation Level: 3 at 31-60 days overdue."


def _parse_date(value, default_days, today):
    if dateparser is not None:
        try:
            return dateparser.parse(value).date(), False
        except Exception:
            pass

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date(), False
        except Exception:
            pass

    return today - timedelta(days=default_days), True


def _email_body(r):
    first = r["first_name"]
    outlet = r["Outlet"]
    portal = r["Portal"]
    inv = r["Invoice"]
    amount = r["amount_display"]
    due = r["due_date"].strftime("%Y-%m-%d")
    last_date = r["last_fu"].strftime("%Y-%m-%d")
    last_response = r["LastResponse"]
    timing = None

    if r["days_overdue"] > 0:
        timing = "{} days overdue".format(r["days_overdue"])
    elif r["days_until_due"] == 0:
        timing = "due today"
    else:
        timing = "{} days until due".format(r["days_until_due"])

    tones = {
        0: "I hope this note finds you well. This is a friendly nudge on the invoice below; if payment is already scheduled, no action is needed.",
        1: "I wanted to follow up on the invoice below. Could you let me know when payment might be on its way?",
        2: "I would appreciate a quick payment status update. Please let me know the scheduled payment date or any blockers we can help resolve.",
        3: "This invoice is now significantly overdue. Please confirm a payment date by the end of the week so we can avoid further escalation.",
        4: "This is a final notice. If payment is not confirmed immediately, the account will be referred for further collection.",
    }
    tone = tones.get(r["escalation"], "Please update us on the payment status for the invoice below.")

    context = "Last contact: {}".format(last_date)
    if last_response and last_response not in ("", "Unknown"):
        context += "\nTheir last response: \"{}\"".format(last_response)

    return (
        "Hi {first},\n\n"
        "I'm following up on invoice {inv} for {outlet} ({amount}), due {due}. {tone}\n\n"
        "Portal: {portal}\n"
        "Invoice: {inv}\n"
        "Amount: {amount}\n"
        "Due date: {due}\n"
        "Status: {timing}\n"
        "{context}\n\n"
        "Thank you for your help with {outlet}.\n"
        "Best regards,\n"
        "[Your name]"
    ).format(
        first=first,
        outlet=outlet,
        inv=inv,
        amount=amount,
        due=due,
        tone=tone,
        portal=portal,
        timing=timing,
        context=context,
    )


def process(text: str) -> str:
    """Convert pasted pipe-delimited invoice records into a ranked follow-up sequence and email drafts."""
    if not text.strip():
        return "Paste pipe-delimited invoice records to generate a ranked follow-up sequence and email drafts.\n\n" + REFERENCE_LINE

    today = date.today()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    records = []

    for line in lines:
        parts = [part.strip() for part in line.split("|")]
        if not any(parts):
            continue

        # Mark incomplete when any required field is absent/blank.
        incomplete = len(parts) < 11 or any(not part for part in parts[:11])

        record = {}
        for i, key in enumerate(FIELDS):
            record[key] = parts[i] if i < len(parts) and parts[i] else DEFAULTS[i]
        record["incomplete"] = incomplete

        issued, issued_unc = _parse_date(record["Issued"], 30, today)
        last_fu, last_unc = _parse_date(record["LastFollowup"], 7, today)
        record["date_uncertain"] = issued_unc or last_unc

        terms_match = re.search(r"\d+", record["TermsDays"])
        terms = int(terms_match.group()) if terms_match else 30

        raw_amount = str(record["Amount"]).replace("$", "").replace(",", "").strip()
        try:
            amount = float(raw_amount)
            amount_missing = math.isnan(amount)
            if amount_missing:
                amount = 0.0
        except ValueError:
            amount = 0.0
            amount_missing = True

        count_match = re.search(r"\d+", str(record["FollowupCount"]))
        followup_count = int(count_match.group()) if count_match else 0

        due_date = issued + timedelta(days=terms)
        days_overdue = max((today - due_date).days, 0)
        days_until_due = max((due_date - today).days, 0)
        days_since_last_followup = max((today - last_fu).days, 0)
        age_days = (today - issued).days

        if days_overdue == 0:
            escalation = 0
        elif days_overdue <= 14:
            escalation = 1
        elif days_overdue <= 30:
            escalation = 2
        elif days_overdue <= 60:
            escalation = 3
        else:
            escalation = 4

        if followup_count >= 2 and days_overdue > 14:
            escalation += 1
        escalation = min(escalation, 4)

        if days_overdue > 0:
            priority = days_overdue * 10 + int(round(amount / 100)) + days_since_last_followup * 2
        else:
            priority = -days_until_due

        record.update({
            "issued": issued,
            "last_fu": last_fu,
            "terms": terms,
            "amount": amount,
            "amount_missing": amount_missing,
            "followup_count": followup_count,
            "due_date": due_date,
            "days_overdue": days_overdue,
            "days_until_due": days_until_due,
            "days_since_last_followup": days_since_last_followup,
            "age_days": age_days,
            "escalation": escalation,
            "priority": priority,
            "first_name": record["Contact"].split()[0] if record["Contact"] not in ("", "Unknown") else "there",
            "amount_display": "Unknown" if amount_missing else "${:,.0f}".format(amount),
        })

        records.append(record)

    if not records:
        return "No pipe-delimited invoice records found. Paste lines with fields separated by vertical bars.\n\n" + REFERENCE_LINE

    records.sort(key=lambda r: r["priority"], reverse=True)

    out = ["## 1. RANKED FOLLOW-UP SEQUENCE", ""]

    for i, record in enumerate(records, 1):
        if record["days_overdue"] > 0:
            status = "{} days overdue".format(record["days_overdue"])
        elif record["days_until_due"] == 0:
            status = "due today"
        else:
            status = "{} days until due".format(record["days_until_due"])

        name = record["Outlet"] + (" (incomplete)" if record["incomplete"] else "")

        out.append("{}. {}".format(i, name))
        out.append("   Portal: {}".format(record["Portal"]))
        out.append("   Contact: {}".format(record["Contact"]))
        out.append("   Invoice: {}".format(record["Invoice"]))
        out.append("   Amount: {}".format(record["amount_display"]))
        out.append("   Due date: {}".format(record["due_date"].strftime("%Y-%m-%d")))
        out.append("   Days status: {}".format(status))
        out.append("   Escalation Level: {}".format(record["escalation"]))
        out.append("")

    out.append("## 2. EMAIL DRAFTS")
    out.append("")

    emails = []

    for i, record in enumerate(records, 1):
        subject = "Invoice {invoice} for {amount} — follow-up {number}".format(
            invoice=record["Invoice"],
            amount=record["amount_display"],
            number=record["followup_count"] + 1,
        )
        body = _email_body(record)
        emails.append("Subject: {}\n\n{}".format(subject, body))

        out.append("### {}. {} — {}".format(i, record["Outlet"], record["Invoice"]))
        out.append("")
        out.append("Subject: {}".format(subject))
        out.append("")
        out.append(body)

        if i < len(records):
            out.append("")
            out.append("---")
            out.append("")

    out.append("## 3. NEXT ESCALATION THRESHOLDS")
    out.append("")
    out.append("Level 0 - Not overdue / due today")
    out.append("Level 1 - 1-14 days overdue")
    out.append("Level 2 - 15-30 days overdue")
    out.append("Level 3 - 31-60 days overdue")
    out.append("Level 4 - >60 days overdue, or 15+ days overdue with 2+ follow-ups")
    out.append("")
    out.append(REFERENCE_LINE)
    out.append("")
    out.append("## COPY-PASTE BATCH BLOCK")
    out.append("")
    out.append("```text")
    out.append("\n\n---\n\n".join(emails))
    out.append("```")

    return "\n".join(out)


def _cli_main():
    print(process(sys.stdin.read()))


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()