# snowflake-ai-evaluation

An end-to-end AI agent evaluation pipeline using Snowflake TPC-H data, dbt, LangGraph, and the Claude API. Demonstrates how to build trustworthy evaluation pipelines for LLM-powered agents.

**Stack:** dbt · Snowflake · LangGraph · OpenAI API (agent) · Gemini API (agent) · Claude API (evaluator) · Streamlit · Python 3.11+

---

## Architecture

```
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1  (read-only source)
        │
        ▼
dbt Transform Layer
  ANALYTICS_DB.STAGING      — stg_* views
  ANALYTICS_DB.MARTS        — mart_* tables (agent-ready)
        │
        ▼
LangGraph Agent  (src/agent/)
  Queries mart tables · Answers customer support questions via OpenAI or Gemini
  Swap agents with --agent openai | gemini
        │
        ▼
Evaluation Pipeline  (src/evaluation/)
  Scores responses against golden test suite · Writes to ANALYTICS_DB.EVALUATION
        │
        ▼
Streamlit App  (app/)
  Interactive chat · Evaluation dashboard
```

---

## Prerequisites

- Python 3.11+
- A Snowflake account ([free trial](https://signup.snowflake.com/) works)
- An [OpenAI API key](https://platform.openai.com/api-keys) (default agent)
- A [Google AI Studio API key](https://aistudio.google.com) — free, no credit card required (Gemini agent)
- An [Anthropic API key](https://console.anthropic.com/) (Claude evaluator)

---

## 1. Clone and install

```bash
git clone https://github.com/hhphan/snowflake-ai-evaluation
cd snowflake-ai-evaluation

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt
```

---

## 2. Snowflake setup

### 2.1 Create the output database

Run this once in a Snowflake worksheet (the TPC-H source already exists):

```sql
CREATE DATABASE IF NOT EXISTS ANALYTICS_DB;
```

The three schemas (`STAGING`, `MARTS`, `EVALUATION`) are created automatically by dbt on first run.

### 2.2 Warehouses (optional but recommended)

```sql
CREATE WAREHOUSE IF NOT EXISTS TRANSFORM_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

CREATE WAREHOUSE IF NOT EXISTS REPORTING_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;
```

If you skip this, use your existing `COMPUTE_WH` and update `SNOWFLAKE_WAREHOUSE` in `.env`.

---

## 3. Environment variables

```bash
cp .env.example .env
```

Snowflake credentials live in `~/.dbt/profiles.yml` (see step 4) — the Python app reads them from there too, so you don't need to duplicate them in `.env`. Only add the non-Snowflake values:

```bash
# Agent — OpenAI (default)
OPENAI_API_KEY=sk-...

# Agent — Gemini (free at aistudio.google.com)
GOOGLE_API_KEY=your-key-here

# Which agent to use: openai | gemini  (overridden by --agent flag at runtime)
AGENT_NAME=openai

# Anthropic — used by the evaluation scorer (Claude as judge)
ANTHROPIC_API_KEY=sk-ant-...

# Evaluation config
EVAL_MODEL=claude-sonnet-4-6
EVAL_SCORE_THRESHOLD=0.75
EVAL_PASS_RATE_THRESHOLD=0.85

# App
STREAMLIT_PORT=8501
LOG_LEVEL=INFO
```

---

## 4. dbt setup

### 4.1 Configure the dbt profile

Both dbt and the Python app (`src/utils/snowflake_client.py`) read Snowflake credentials from `~/.dbt/profiles.yml` — it is the single source of truth. No Snowflake variables are needed in `.env`.

```bash
cp dbt_project/profiles.yml.example ~/.dbt/profiles.yml
```

Then edit `~/.dbt/profiles.yml` and fill in your Snowflake credentials:

```yaml
snowflake_ai_evaluation:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: your_org-your_account    # e.g. abc12345.us-east-1
      user: your_username
      password: your_password
      role: ACCOUNTADMIN
      database: ANALYTICS_DB
      warehouse: TRANSFORM_WH           # or COMPUTE_WH
      schema: PUBLIC
      threads: 4
```

### 4.2 Verify the Python connection

```bash
python scripts/verify_snowflake.py
```

Expected output:

```
Connected successfully:
  User      : your_username
  Role      : ACCOUNTADMIN
  Database  : ANALYTICS_DB
  Warehouse : TRANSFORM_WH
```

This confirms that `snowflake_client.py` can read your `profiles.yml` and reach Snowflake.

### 4.3 Verify the dbt connection

```bash
cd dbt_project
dbt debug
```

You should see `All checks passed!`. If not, double-check your account identifier — it must match the format shown in your Snowflake URL (e.g. `abc12345.us-east-1`).

### 4.4 Install dbt packages

```bash
dbt deps
```

This installs `dbt_utils` declared in `packages.yml`.

---

## 5. Run the dbt pipeline (Part 1)

```bash
cd dbt_project

# seed + run + test in one command
# mart_eval_results_summary is excluded — it needs the evaluation pipeline (Part 2) first
dbt build --exclude mart_eval_results_summary
```

Or run the steps individually if you want more control:

```bash
dbt seed                                        # load golden test suite CSV
dbt run  --exclude mart_eval_results_summary    # build staging + intermediate + mart
dbt test --exclude mart_eval_results_summary    # run schema tests
```

After a successful run you should have:

| Schema | Object | Type |
|---|---|---|
| `ANALYTICS_DB.STAGING` | `STG_TPCH__ORDERS`, `STG_TPCH__CUSTOMERS`, etc. | Views |
| `ANALYTICS_DB.MARTS` | `MART_CUSTOMER_SUPPORT_CONTEXT` | Table (~6M rows) |
| `ANALYTICS_DB.EVALUATION` | `GOLDEN_CUSTOMER_SUPPORT` | Table (10 rows, from seed) |

---

## 6. Run the LangGraph agent (Part 2)

The agent queries `MART_CUSTOMER_SUPPORT_CONTEXT` and answers order questions. The default provider is OpenAI (`gpt-4o`). Set `AGENT_NAME=gemini` in `.env` to use Gemini instead.

```bash
# interactive CLI — uses AGENT_NAME from .env (default: openai)
python -m src.agent.graph
```

Example questions:
- `What is the status of order 1?`
- `When was order 3 shipped?`
- `What items are in order 5?`

---

## 7. Run the evaluation pipeline (Part 3)

The pipeline runs the agent on every question in the golden test suite, scores each response using Claude as an LLM judge, and writes results to `ANALYTICS_DB.EVALUATION.EVAL_RESULTS`.

```bash
# run a single agent
python -m src.evaluation.pipeline --agent openai
python -m src.evaluation.pipeline --agent gemini

# smoke test — first N questions only
python -m src.evaluation.pipeline --agent openai --limit 2

# compare both agents back-to-back
python -m src.evaluation.pipeline --agent openai && python -m src.evaluation.pipeline --agent gemini
```

The pipeline exits 0 if both thresholds are met, 1 otherwise:

| Threshold | Default | Description |
|-----------|---------|-------------|
| `EVAL_SCORE_THRESHOLD` | `0.75` | Minimum score for a single question to pass |
| `EVAL_PASS_RATE_THRESHOLD` | `0.85` | Minimum fraction of questions that must pass |

After the first run, build the summary mart so the dashboard has data:

```bash
cd dbt_project
dbt run --select mart_eval_results_summary
```

---

## 8. Streamlit app (Part 3)

```bash
streamlit run app/streamlit_app.py
```

Opens at `http://localhost:8501` with two pages:

- **Chat** — talk to the agent directly; choose OpenAI or Gemini from the sidebar selector
- **Evaluation Dashboard** — filter by agent, compare pass rate and P90 score side-by-side across runs

> The dashboard requires at least one completed eval run and the `mart_eval_results_summary` mart to be built (step 7 above).

---

## 9. Browse the lineage DAG (optional)

```bash
dbt docs generate && dbt docs serve
```

---

## Common Commands

```bash
# dbt
dbt debug                          # verify Snowflake connection
dbt deps                           # install packages
dbt seed                           # load golden test suite
dbt run                            # run all models
dbt run --select staging.*         # run staging only
dbt test                           # run all tests
dbt docs generate && dbt docs serve

# Agent (Part 2)
python -m src.agent.graph

# Evaluation pipeline (Part 3)
python -m src.evaluation.pipeline --agent openai
python -m src.evaluation.pipeline --agent gemini
python -m src.evaluation.pipeline --agent openai --limit 2    # quick smoke test

# Streamlit app (Part 3)
streamlit run app/streamlit_app.py

# Tests
pytest tests/unit/
pytest tests/integration/ -m slow

# Lint
ruff check src/
sqlfluff lint dbt_project/models/
```

---

## Database / Schema Layout

```
SNOWFLAKE_SAMPLE_DATA        read-only TPC-H source — never write here
  └── TPCH_SF1

ANALYTICS_DB                 all project outputs
  ├── STAGING                dbt staging views
  ├── MARTS                  dbt mart tables (agent + Streamlit)
  └── EVALUATION             eval results + golden test suite
```
