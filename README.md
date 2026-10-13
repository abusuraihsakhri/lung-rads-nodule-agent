# Lung-RADS Nodule Agent

A Python library, command-line utility and standalone browser interface for a **limited subset** of ACR Lung-RADS v2022 screening nodule size rules. Separate legacy modules provide a rule-based synthetic metric audit API and CLI.

**Clinical limitation:** The classification tool is educational and not a validated clinical decision-support system. It does not implement Lung-RADS category 0, airway nodules, atypical pulmonary cysts, suspected infection/inflammation, benign morphological exceptions, complete longitudinal follow-up/stepped management, or screening eligibility. Do not use the output alone for clinical decisions; refer to the [official ACR Lung-RADS guidance](https://www.acr.org/Clinical-Resources/Reporting-and-Data-Systems/Lung-Rads).

## Browser interface

Open `web/index.html` directly in a current browser, or serve it locally:

```bash
python -m http.server 8080 --directory web
# Open http://localhost:8080
```

Add one or more nodules, select solid, part-solid or pure ground-glass type, enter mean diameters, and select **Assess nodules**. The tool shows the highest supported category, management text, an optional separate **S modifier**, and downloadable JSON. It uses vanilla JavaScript with no server, external API, analytics or persistent browser storage; measurements remain in memory until you close or reload the page. Only enter de-identified data.

GitHub Pages publishing is configured via `.github/workflows/pages.yml`; a live link will be added when deployment is verified.

## Python installation and assessment CLI

Requires Python 3.9 or later.

```bash
git clone https://github.com/abusuraihsakhri/lung-rads-nodule-agent.git
cd lung-rads-nodule-agent
python -m pip install -e '.[server,dev]'
```

```bash
lung-rads-assess assess -n solid:7 -n part-solid:10::4 --json
lung-rads-assess categorize solid 8
lung-rads-assess categorize part-solid 10 --solid-component 6
lung-rads-assess info 4A
```

For `assess`, a nodule specification is `TYPE:TOTAL_MM[:PRIOR_TOTAL_MM[:SOLID_MM[:PRIOR_SOLID_MM]]]`. For a baseline part-solid nodule, leave the prior measurement blank: `part-solid:10::4`. A solid component measurement is required for part-solid nodules at least 6 mm. A supplied prior diameter is assumed to be from the previous 12 months unless the Python `Nodule.prior_interval_months` field is set explicitly. Growth means **strictly more than 1.5 mm over 12 months**.

The separate Python API provides `Nodule`, `categorize_nodule` and `assess_screening` from the `lung_rads_nodule_agent` package. Significant non-nodule findings add `s_modifier=True`; they do not replace the numeric Lung-RADS category.

## Legacy demonstration audit and API

The generic metric-audit features are not a clinical Lung-RADS categorization pathway. They use illustrative thresholds, synthetic case identifiers and a deterministic mock responder.

```bash
lung-rads-nodule-engine audit --case-id SYNTH-001 --primary 26.2 --secondary 12.5
lung-rads-nodule-engine batch -i sample.csv -o results.csv
lung-rads-nodule-engine chat "system status"
lung-rads-nodule-engine serve --host 127.0.0.1 --port 8000
```

The package's FastAPI server exposes `/health`, `/api/audit`, and `/api/chat`. A second legacy FastAPI app, `agents.api:app`, exposes `/metrics` and an in-memory signed audit ledger and accepts a different `SystemTaskPayload` schema:

```bash
uvicorn agents.api:app --host 127.0.0.1 --port 8001
```

Only the mock responder is implemented. No cloud LLM provider is connected. Audit events use chained HMAC-SHA256 signatures in **memory**; this is not durable log storage and cannot prove HIPAA compliance. The identifier filter uses a limited set of patterns and is not a complete PHI de-identification solution. Never submit real patient information to these demonstration endpoints.

For container deployment, provide a persistent random `AUDIT_SECRET_KEY` first:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

Docker serves the package FastAPI application on port 8000; it does not serve the browser interface.

## Tests and development

```bash
python -m pip install -e '.[server,dev]'
python -m pip check
pytest -v
node --test tests/test_web.cjs   # Node.js 22+
```

CI runs Python 3.10, 3.11 and 3.12 tests, syntax/dependency checks, browser-rule tests and a signed-log integrity smoke test. The browser interface runs in current Chrome, Firefox, Safari and Edge where modern JavaScript and Blob downloads are supported; automated visual cross-browser verification has not been performed.

## Technology and license

Python standard library, Pydantic 2, optional FastAPI/Uvicorn, HTML/CSS/JavaScript, pytest, Node test runner, Docker and GitHub Actions. MIT license; see [LICENSE](LICENSE).
