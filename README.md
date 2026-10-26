![Hacktoberfest 2026 Open-Source AI Challenge Week 3: Slow and Steady](docs/images/hfcw3.webp)

# Paper to Portfolio

Found an old share certificate in a drawer? Paper to Portfolio reads it with a local
open-weight model, traces every bonus, split, merger and rename since the day it was
printed, and tells you what it is worth today and how to claim it.

Thousands of Indian families hold physical shares bought in the 1980s and 90s. The
company has usually been renamed or merged, the share count has multiplied several
times, and unclaimed dividends may have been moved to the IEPF. Working that out by hand
takes weeks, or a paid recovery firm. Here it takes a few slow minutes on a laptop with
no GPU.

## How it works

1. **Read.** Gemma (`gemma4:e4b`, via Ollama) reads the certificate photo into structured
   fields: company, holder, folio, certificate number, shares, face value, issue date. You
   check and correct them.
2. **Extract.** You paste the company's corporate-announcement history (from the exchange
   website or annual reports). Gemma lists every event that changes the share count or the
   company name, and must quote the sentence it relied on.
3. **Verify.** Plain Python throws out any event whose quote is not found word for word in
   your text, or whose ratio is missing. The model cannot slip in an invented bonus.
4. **Compute.** Plain Python, not the model, walks the share count forward with exact
   fractions, flooring as Indian companies do (fractional entitlements are paid in cash).
5. **Explain.** Gemma writes a short plain-language summary in English, Hindi, Marathi,
   Bengali or Tamil, using only the computed numbers. The claim checklist (IEPF search, RTA,
   KYC, transmission, demat, IEPF-5) is fixed text, never generated.

Everything runs locally. A certificate holds a family's name and folio number, so nothing
leaves the machine.

## Run it

Needs Python 3.12+ and [Ollama](https://ollama.com) with Gemma pulled:

```bash
ollama pull gemma4:e4b
python -m p2p.server        # open http://localhost:8765
```

Click **Use fictional sample** to try it with the specimen certificate in `samples/`.
On a CPU-only laptop, reading takes about a minute and a half and tracing a few minutes.
Slow and steady.

Settings via environment: `P2P_MODEL` (default `gemma4:e4b`), `OLLAMA_URL`, `PORT`.

## Tests

```bash
python -m unittest -v
```

The tests cover the share arithmetic, fraction handling, evidence verification and the
checklist. They need no model, so they also run in GitHub Actions on every push.

## Sample data

`samples/sample_certificate.png` and `samples/sample_actions.txt` describe a made-up
company and holder. Regenerate the image with `python samples/make_sample_certificate.py`.

## Disclaimer

General guidance, not legal or financial advice. Confirm with the company's Registrar and
Transfer Agent or the IEPF Authority before filing anything.

## License

MIT
