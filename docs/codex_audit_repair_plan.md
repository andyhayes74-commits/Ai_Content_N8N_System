# Codex Audit Repair Plan

## Purpose

This document tracks remediation work for the Codex audit performed against merge baseline `b4241b1`.

The audit correctly identified a release-risk gap:

- committed workflow JSON on GitHub did not match the generated/live-ready workflow JSON produced during validation/preflight.
- CI checks passed because generators rewrote workflows before validation.
- direct GitHub imports could therefore import stale/minimal workflows.

This repair branch exists to eliminate that drift.

---

# Confirmed Audit Findings

## Confirmed valid

### 1. Workflow drift between committed JSON and generated JSON

Confirmed.

The generated workflows include:

- OpenAI/LiteLLM HTTP Request nodes
- live-mode request generation
- model error persistence
- Google Drive REST request structure
- dry-run/live-mode branching

The committed workflow JSON on `main` was stale/minimal.

Risk level: HIGH.

---

### 2. Validation regenerated workflows before checking them

Confirmed.

`validate_repo.sh`
`pre_n8n_readiness_check.py`
`n8n_import_preflight.sh`

all regenerated workflows before validation.

This allowed CI to validate generated artifacts rather than the committed repository state.

Risk level: HIGH.

---

### 3. README wording overstated committed workflow readiness

Confirmed.

The README described generated/live-ready capability while the committed workflow JSON still represented minimal versions.

Risk level: MEDIUM.

---

## Partially valid / operational caveats

### Google Drive auth structure

The audit correctly notes that imported workflows still require:

- OAuth credentials
- environment configuration
- runtime credential assignment in n8n

This remains expected operational setup work.

The repository does not claim live credential execution was completed.

Risk level: MEDIUM.

---

### SQL interpolation risk

Some workflows interpolate request values into SQL strings.

Current webhook secret gates reduce exposure.

Further hardening should:

- normalize more scalar fields
- centralize escaping patterns
- eventually migrate to parameterized query support where practical inside n8n

Risk level: MEDIUM.

---

# Repair Actions

Status: implemented on the transfer-ready repair branch. Remaining caveats are runtime-only credential and sandbox execution checks.

## Phase 1 — Commit generated workflows

Implemented. Required:

- regenerate all LLM workflows
- regenerate all Drive workflows
- embed task-specific prompts
- repair expression braces
- commit final generated workflow JSON into repository

Result:

The committed repository state becomes identical to the validated/preflight state.

---

## Phase 2 — Add workflow drift guard

Implemented through `scripts/check_workflow_drift.sh`. CI/preflight must fail if:

```bash
python scripts/build_llm_workflows.py
python scripts/embed_llm_prompts.py
python scripts/build_drive_workflows.py
python scripts/fix_generated_n8n_expressions.py
```

changes committed workflow JSON.

Expected enforcement:

```bash
git diff --exit-code workflows/
```

This prevents silent workflow drift.

---

## Phase 3 — Documentation clarification

Implemented. README and operational docs must clearly distinguish:

- committed workflow JSON
- generated workflow JSON
- runtime-generated artifacts
- live-tested integrations

The repo should continue using the label:

```text
v1.0 RC pre-n8n transfer baseline
```

not production-ready.

---

## Phase 4 — Runtime hardening follow-up

Partially implemented for repository-transfer hardening. Post-import hardening tasks:

- further parameterized-query migration where practical inside n8n
- stronger Google Drive credential handling
- live OAuth validation
- sandbox execution validation
- runtime backup/export workflow
- GitHub drift detection workflow

---

# Definition Of Fixed

The Codex audit findings are considered repaired when:

- committed workflows match generated workflows
- CI detects workflow drift
- direct GitHub imports no longer import stale workflows
- README wording matches repository reality
- preflight validates committed state rather than regenerated-only state

---

# Remaining Honest Caveat

Even after repair:

- live OpenAI execution
- live Google Drive execution
- live Postgres execution
- live OpenClaw/Hermes callbacks

still require sandbox runtime testing inside n8n.
