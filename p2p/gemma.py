"""Thin client for a local Gemma model served by Ollama.

Gemma does the reading (certificate image, messy filing text) and the writing
(plain-language summary). It never does the arithmetic; see ledger.py.
"""
import base64
import json
import os
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("P2P_MODEL", "gemma4:e4b")
TIMEOUT = 900  # CPU inference is slow; that's fine, we're in no hurry

CERTIFICATE_SCHEMA = {
    "type": "object",
    "properties": {
        "company": {"type": "string"},
        "holder": {"type": "string"},
        "folio": {"type": "string"},
        "certificate_no": {"type": "string"},
        "shares": {"type": "integer"},
        "face_value": {"type": "number"},
        "issue_date": {"type": "string", "description": "YYYY-MM-DD"},
    },
    "required": ["company", "holder", "folio", "certificate_no", "shares", "face_value", "issue_date"],
}

ACTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "type": {"type": "string", "enum": ["bonus", "split", "consolidation", "merger", "rename"]},
                    "give": {"type": "integer", "description": "bonus/merger: shares received, else 0"},
                    "per": {"type": "integer", "description": "bonus/merger: per this many shares held, else 0"},
                    "from_fv": {"type": "number", "description": "split/consolidation: old face value, else 0"},
                    "to_fv": {"type": "number", "description": "split/consolidation: new face value, else 0"},
                    "into": {"type": "string", "description": "merger/rename: company name afterwards, else empty"},
                    "evidence": {"type": "string", "description": "exact sentence copied from the text"},
                },
                "required": ["date", "type", "give", "per", "from_fv", "to_fv", "into", "evidence"],
            },
        }
    },
    "required": ["actions"],
}


def _chat(messages, schema=None, temperature=0.0):
    body = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if schema:
        body["format"] = schema
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        content = json.load(resp)["message"]["content"]
    return json.loads(content) if schema else content.strip()


def read_certificate(image_bytes):
    prompt = (
        "This is a photo of an old Indian physical share certificate. "
        "Read it and return the company name, registered holder, folio number, "
        "certificate number, number of shares, face value per share in rupees, "
        "and the issue date as YYYY-MM-DD. Copy names exactly as printed."
    )
    return _chat(
        [{"role": "user", "content": prompt, "images": [base64.b64encode(image_bytes).decode()]}],
        schema=CERTIFICATE_SCHEMA,
    )


def extract_actions(company, text):
    prompt = (
        f"Below are corporate announcements for {company} and any company it later became.\n"
        "List every event that changes the NUMBER of shares or the COMPANY NAME:\n"
        "- bonus: 'give' new shares for every 'per' shares held (ratio 1:2 means give=1, per=2)\n"
        "- split / consolidation: face value from 'from_fv' to 'to_fv'\n"
        "- merger: 'give' shares of company 'into' for every 'per' shares held\n"
        "- rename: new name in 'into'\n"
        "Fill every field; use 0 or an empty string for fields that do not apply. "
        "Write dates as YYYY-MM-DD.\n"
        "Ignore dividends, meetings and anything else. For each event, 'evidence' must be "
        "the exact sentence copied word for word from the text. Do not invent events.\n\n"
        f"TEXT:\n{text}"
    )
    return _chat([{"role": "user", "content": prompt}], schema=ACTIONS_SCHEMA)["actions"]


def write_summary(certificate, result, language="English"):
    facts = json.dumps({"certificate": certificate, "result": result}, ensure_ascii=False, indent=1)
    prompt = (
        f"Write a short, warm explanation in {language} for a family that just found this old "
        "share certificate. Explain in plain words what happened to the shares over the years "
        "and what they hold today, then the first two things they should do next. "
        "Use ONLY the numbers in the facts below; do not compute or invent anything. "
        "Under 180 words. No markdown headings.\n\n"
        f"FACTS:\n{facts}"
    )
    return _chat([{"role": "user", "content": prompt}], temperature=0.3)
