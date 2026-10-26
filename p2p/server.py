"""Local web app: python -m p2p.server, then open http://localhost:8765"""
import base64
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import claim, gemma, ledger

INDEX = Path(__file__).with_name("index.html")
SAMPLES = Path(__file__).parent.parent / "samples"
SAMPLE_FILES = {
    "/sample/certificate.png": ("sample_certificate.png", "image/png"),
    "/sample/actions.txt": ("sample_actions.txt", "text/plain"),
}
PORT = int(os.environ.get("PORT", "8765"))


def handle_read(payload):
    return gemma.read_certificate(base64.b64decode(payload["image_b64"]))


def handle_trace(payload):
    certificate = payload["certificate"]
    text = payload["actions_text"]
    proposed = gemma.extract_actions(certificate["company"], text)
    accepted, rejected = ledger.verify(proposed, text)
    result = ledger.trace(certificate, accepted)
    result["rejected"] = rejected
    result["value_today"] = ledger.value(result["shares_today"], float(payload.get("price") or 0))
    result["checklist"] = claim.checklist(certificate, result, payload.get("holder_deceased", False))
    result["summary"] = gemma.write_summary(certificate, {
        k: result[k] for k in ("company_today", "shares_today", "growth", "value_today", "timeline")
    }, payload.get("language", "English"))
    return result


ROUTES = {"/api/read": handle_read, "/api/trace": handle_trace}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        if not content_type.startswith("image/"):
            content_type += "; charset=utf-8"
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, INDEX.read_bytes(), "text/html")
        elif self.path in SAMPLE_FILES:
            name, content_type = SAMPLE_FILES[self.path]
            self._send(200, (SAMPLES / name).read_bytes(), content_type)
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        route = ROUTES.get(self.path)
        if not route:
            return self._send(404, {"error": "not found"})
        try:
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self._send(200, route(payload))
        except Exception as exc:  # surface model/network errors to the page
            self._send(500, {"error": f"{type(exc).__name__}: {exc}"})


def main():
    print(f"Paper to Portfolio on http://localhost:{PORT}  (model: {gemma.MODEL})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
