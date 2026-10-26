"""Deterministic share arithmetic. No model output is trusted here without a check.

Indian practice: fractional entitlements from bonus or merger ratios are pooled,
sold by the company, and paid out in cash, so we floor and record the fraction.
"""
import re
from datetime import date, datetime
from fractions import Fraction

DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d %b %Y", "%d %B %Y")
REQUIRED = {
    "bonus": ("give", "per"),
    "merger": ("give", "per", "into"),
    "split": ("from_fv", "to_fv"),
    "consolidation": ("from_fv", "to_fv"),
    "rename": ("into",),
}


def normalise(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def parse_date(value):
    """Indian filings write DD-MM-YYYY; models sometimes echo that back. Accept both."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    raise ValueError(f"unrecognised date: {value!r}")


def _missing(action):
    fields = REQUIRED.get(action.get("type"))
    if fields is None:
        return "unknown event type"
    empty = [f for f in fields if not action.get(f)]
    if empty:
        return f"missing {', '.join(empty)}"
    try:
        parse_date(action.get("date"))
    except ValueError as exc:
        return str(exc)
    return None


def verify(actions, source_text):
    """Keep only complete actions whose evidence appears verbatim in the source text."""
    haystack = normalise(source_text)
    accepted, rejected = [], []
    for action in actions:
        evidence = normalise(action.get("evidence"))
        problem = _missing(action)
        if not (len(evidence) >= 15 and evidence in haystack):
            problem = "evidence not found in the pasted text"
        if problem:
            rejected.append({**action, "reason": problem})
        else:
            accepted.append({**action, "date": parse_date(action["date"]).isoformat()})
    return accepted, rejected


def _multiplier(action):
    kind = action["type"]
    if kind == "bonus":
        return 1 + Fraction(action["give"], action["per"])
    if kind == "merger":
        return Fraction(action["give"], action["per"])
    if kind in ("split", "consolidation"):
        return Fraction(str(action["from_fv"])) / Fraction(str(action["to_fv"]))
    if kind == "rename":
        return Fraction(1)
    raise ValueError(f"unknown action type: {kind}")


def _describe(action):
    kind = action["type"]
    if kind == "bonus":
        return f"Bonus {action['give']}:{action['per']}"
    if kind == "merger":
        return f"Merged into {action['into']} ({action['give']} for every {action['per']})"
    if kind in ("split", "consolidation"):
        return f"{kind.title()}: face value Rs {action['from_fv']:g} to Rs {action['to_fv']:g}"
    return f"Renamed to {action['into']}"


def trace(certificate, actions):
    """Walk the share count forward from the certificate date through each action."""
    issued = parse_date(certificate["issue_date"])
    shares = int(certificate["shares"])
    company = certificate["company"]
    face_value = float(certificate["face_value"])
    timeline = [{
        "date": issued.isoformat(),
        "event": "Certificate issued",
        "company": company,
        "shares": shares,
        "face_value": face_value,
    }]
    skipped = []
    for action in sorted(actions, key=lambda a: a["date"]):
        if date.fromisoformat(action["date"]) <= issued:
            skipped.append({**action, "reason": "happened before the certificate was issued"})
            continue
        exact = shares * _multiplier(action)
        shares = int(exact)  # floor; the fraction is paid in cash
        if action["type"] in ("merger", "rename"):
            company = action["into"]
        if action["type"] in ("split", "consolidation"):
            face_value = float(action["to_fv"])
        timeline.append({
            "date": action["date"],
            "event": _describe(action),
            "company": company,
            "shares": shares,
            "face_value": face_value,
            "fraction_paid_in_cash": float(exact - shares),
            "evidence": action.get("evidence", ""),
        })
    return {
        "company_today": company,
        "shares_today": shares,
        "face_value_today": face_value,
        "growth": f"{shares / int(certificate['shares']):g}x",
        "timeline": timeline,
        "skipped": skipped,
    }


def value(shares, price):
    return round(shares * price, 2) if price else None
