# Lung Rads Nodule Agent

> **Domain:** Diagnostic Radiology & Medical Imaging AI
> **Reference Guidelines & Standards:** `American College of Radiology (ACR) RADS & Fleischner Society`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Lung Rads Nodule Agent** is an advanced analytical and computational platform implementing ACR Lung-RADS v2022 Low-Dose CT Screening Supervisor. It provides:

- **Lung-RADS Categorization**: Automated categorization of pulmonary nodules into Lung-RADS categories (1, 2, 3, 4A, 4B, 4X, S) based on nodule type, size, growth, and suspicious features.
- **Multi-Agent Clinical Audit**: Distributed component architecture with specialized sub-agents for morphology analysis, kinetics evaluation, and biomarker concordance.
- **Zero-PHI Protection**: Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers from outbound data.
- **Tamper-Evident Audit Trail**: Chained, cryptographically signed HMAC-SHA256 logs for every evaluation and state transition.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`Severity`** — dedicated module for severity evaluation and state verification.
- **`DomainKnowledgeRegistry`**: Enterprise domain rules, guideline matrices, and evidence benchmarks.
- **`AgentAlert`** — dedicated module for agent alert evaluation and state verification.
- **`NoduleMorphologyAgent`**: Specialized Sub-Agent 1 for lung-rads-nodule-agent
- **`LungRADSCategorizerAgent`**: Specialized Sub-Agent 2 for lung-rads-nodule-agent
- **`LongitudinalGrowthAuditorAgent`**: Specialized Sub-Agent 3 for lung-rads-nodule-agent
- **`ClinicalDomainEngine`**: Clinical domain evaluation engine for multi-agent case auditing with configurable thresholds.

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/lung-rads-nodule-agent.git
cd lung-rads-nodule-agent

# Install dependencies
pip install -e .

# For development (includes testing)
pip install pytest
```

---

## 💻 CLI Quickstart & Usage

### 1. Lung-RADS Categorization CLI

#### Assess multiple nodules:
```bash
python cli.py assess -n solid:7 -n part-solid:10:8 --json
```

#### Categorize a single nodule:
```bash
python cli.py categorize solid 7
```

#### Show category information:
```bash
python cli.py info 4A
```

### 2. Clinical Audit CLI

#### Run single case audit:
```bash
python lung_rads_nodule_agent_app.py audit --case-id CASE-001 --primary 26.2 --secondary 12.5 --stat
```

#### Batch process CSV records:
```bash
python lung_rads_nodule_agent_app.py batch -i sample.csv -o results.csv
```

#### Query the supervisory chat:
```bash
python lung_rads_nodule_agent_app.py chat "What is the system status?"
```

#### Launch FastAPI REST server:
```bash
python lung_rads_nodule_agent_app.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--nodule`: Specifies input measurement or parameter value.
- `--new`: Specifies input measurement or parameter value.
- `--suspicious-features`: Specifies input measurement or parameter value.
- `--other-finding`: Specifies input measurement or parameter value.
- `--json`: Specifies input measurement or parameter value.
- `--prior`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_synthetic_id` | Parameter / observation metric | Required |
| `metric_primary` | Parameter / observation metric | Required |
| `metric_secondary` | Parameter / observation metric | Required |
| `is_stat` | Parameter / observation metric | Required |
| `status_flag` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable for persistent audit integrity:

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-random-key"

# Windows
set AUDIT_SECRET_KEY=your-secure-random-key
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 100
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t lung-rads-nodule-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key lung-rads-nodule-agent

# Or use docker-compose
AUDIT_SECRET_KEY=your-secret-key docker-compose up
```

---

## 📁 Project Structure

```
lung-rads-nodule-agent/
├── agents/                          # Enterprise security & multi-agent framework
│   ├── base.py                      # PHI guard, HMAC audit trail, security exceptions
│   ├── models.py                    # Pydantic schemas for tasks and alerts
│   ├── workers.py                   # Specialized domain worker agents
│   ├── supervisor.py                # Master orchestrator
│   ├── llm_factory.py               # LLM client factory (mock, Ollama, Claude, OpenAI)
│   ├── api.py                       # FastAPI REST server
│   ├── metrics.py                   # Prometheus metrics exporter
│   ├── streamer.py                  # WebSocket telemetry streamer
│   └── learning.py                  # Bayesian calibration engine
├── lung_rads_nodule_agent/          # Core Lung-RADS categorization package
│   ├── models.py                    # Data models (Nodule, LungRADSResult, ClinicalCasePayload)
│   ├── engine.py                    # Lung-RADS v2022 categorization engine
│   ├── agents.py                    # Clinical sub-agents and coordinator
│   ├── cli.py                       # Clinical audit CLI
│   └── server.py                    # FastAPI application factory
├── tests/                           # Test suite
│   ├── test_lung_rads.py            # Lung-RADS categorization tests
│   ├── test_lung_rads_nodule_agent.py  # Multi-agent framework tests
│   ├── test_enrichment.py           # Enrichment module tests
│   └── test_validation.py           # Input validation tests
├── cli.py                           # Lung-RADS categorization CLI
├── lung_rads_sentinel.py            # Standalone sentinel application
├── enrichment.py                    # Enrichment feature modules
├── simulator.py                     # High-throughput simulation
├── pyproject.toml                   # Project configuration
├── Dockerfile                       # Container build
└── docker-compose.yml               # Container orchestration
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
