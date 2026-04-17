# iba-digital-worker-guard

> **Govern your digital worker. Human intent declared before the first model fires.**

---

## The Moment

Perplexity just launched a full 24/7 digital worker running on a Mac mini.

19 models. Parallel routing. Multi-day workflows. Runs while you sleep.

Claude Opus for complex reasoning. Gemini for deep research. Grok for fast tasks. Each subtask routed to whichever model is best. All running in parallel. Autonomously. Without you watching.

Who authorized any of it?

---

## The Gap

Which of the 19 models can access your files?
Which can send email on your behalf?
Which can make purchases?
Which can run for 72 hours without a kill threshold?
Which can access your calendar? Your contacts? Your bank?

**Perplexity routes the task to the best model. The best model does what it can do — not what you authorized it to do.**

19 models running in parallel is 19 authorization gaps running in parallel.

The gate has to come before the routing.

---

## The IBA Layer

```
┌─────────────────────────────────────────────────┐
│                HUMAN PRINCIPAL                  │
│   Signs .iba.yaml before the worker starts      │
│   Declares intent, scope, model limits,         │
│   kill threshold, and hard expiry               │
└───────────────────────┬─────────────────────────┘
                        │  Signed Intent Certificate
                        │  · Declared task scope
                        │  · Permitted models
                        │  · Forbidden: purchases, email, files
                        │  · Max runtime / session expiry
                        │  · Kill threshold
                        ▼
┌─────────────────────────────────────────────────┐
│        IBA DIGITAL WORKER GUARD                 │
│   Validates certificate before every            │
│   model invocation, tool call, or action        │
│                                                 │
│   No cert = No worker activation                │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│         YOUR DIGITAL WORKER                     │
│   Perplexity · Claude Code · Custom stacks      │
│   Any multi-model or long-running agent system  │
└─────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
git clone https://github.com/Grokipaedia/iba-digital-worker-guard.git
cd iba-digital-worker-guard
pip install -r requirements.txt
python guard.py "your-digital-worker-task-description" --hollow medium
```

---

## Configuration — .iba.yaml

```yaml
intent:
  description: "Research competitor pricing and draft internal report. No purchases. No external email. No file deletion."

scope:
  - research
  - web_search
  - read
  - draft
  - report
  - internal
  - summarise
  - analyse

denied:
  - purchase
  - payment
  - external_email
  - file_delete
  - calendar_write
  - contact_access
  - credential_access
  - social_post

default_posture: DENY_ALL

kill_threshold: "purchase | payment | send_email_external | file_delete | credential_access"

model_limits:
  max_parallel_models: 5
  permitted_models:
    - claude_opus
    - gemini_pro
    - grok
  forbidden_models:
    - any_uncertified_model

runtime_limits:
  max_session_hours: 8
  max_api_calls: 1000
  interrupt_on_decision: true

temporal_scope:
  hard_expiry: "2026-12-31"

audit:
  chain: witnessbound
  log_every_model_call: true
```

---

## Gate Logic

```
Certificate valid?                          → PROCEED
Action outside declared scope?              → BLOCK
Forbidden action attempted?                 → BLOCK
Uncertified model invoked?                  → BLOCK
API call limit exceeded?                    → BLOCK
Kill threshold triggered?                   → TERMINATE + LOG
Runtime limit exceeded?                     → BLOCK
No certificate present?                     → BLOCK
```

**No cert = No worker activation. No model fires without a valid gate check.**

---

## The Digital Worker Authorization Events

| Action | Without IBA | With IBA |
|--------|-------------|---------|
| Route task to Claude Opus | Implicit — any task | Explicit — declared scope only |
| Route task to Gemini for research | Implicit — any data | Explicit — declared sources only |
| Run for 72 hours overnight | No boundary exists | Hard session expiry enforced |
| Send email to external contact | No boundary exists | FORBIDDEN — BLOCK |
| Make a purchase | No boundary exists | KILL THRESHOLD — TERMINATE |
| Access credentials or passwords | No boundary exists | KILL THRESHOLD — TERMINATE |
| Delete files | No boundary exists | KILL THRESHOLD — TERMINATE |
| Post to social media | No boundary exists | FORBIDDEN — BLOCK |
| Invoke uncertified model | No boundary exists | FORBIDDEN — BLOCK |
| Run 1000+ API calls | No boundary exists | API limit enforced — BLOCK |

---

## Why This Is Different From Every Other Guardrail

Every guardrail operates inside the model's reasoning loop. The safety instruction and the malicious instruction are both text. The model interprets both.

PIArena tested 153 live platforms. Every defense failed.

IBA operates outside the loop entirely. The `.iba.yaml` certificate is not a prompt. It is not a system instruction. It is not a guardrail. It is a cryptographic boundary signed before any model receives its first token.

**You cannot inject a cryptographic boundary.**

When Perplexity routes your task to 19 models — each model invocation is checked against the cert before it fires. The routing intelligence is irrelevant. The cert is absolute.

---

## Live Demo

**governinglayer.com/governor-html/**

Edit the `.iba.yaml`. Type any digital worker action. Watch the gate fire — ALLOW · BLOCK · TERMINATE. Sub-1ms gate latency confirmed.

---

## Patent & Standards Record

```
Patent:   GB2603013.0 (Pending) · UK IPO · Filed February 5, 2026
WIPO DAS: Confirmed April 15, 2026 · Access Code C9A6
PCT:      150+ countries · Protected until August 2028
IETF:     draft-williams-intent-token-00 · CONFIRMED LIVE
          datatracker.ietf.org/doc/draft-williams-intent-token/
NIST:     13 filings · NIST-2025-0035
NCCoE:    10 filings · AI Agent Identity & Authorization
```

IBA priority date: **February 5, 2026**
Perplexity digital worker launch: **April 2026**
IBA predates all known multi-model authorization frameworks.

---

## Related Repos

| Repo | Gap closed |
|------|-----------|
| [iba-governor](https://github.com/Grokipaedia/iba-governor) | Full production governance · working implementation |
| [iba-app-builder-guard](https://github.com/Grokipaedia/iba-app-builder-guard) | App builder · Claude Code routines |
| [agent-vibe-governor](https://github.com/Grokipaedia/agent-vibe-governor) | Vibe coding · token tracking · spend limits |
| [iba-twin-guard](https://github.com/Grokipaedia/iba-twin-guard) | Digital twin identity governance |
| [iba-mythos-governor](https://github.com/Grokipaedia/iba-mythos-governor) | Mythos-ready VulnOps governance |

---

## Acquisition Enquiries

IBA Intent Bound Authorization is available for acquisition.

**Jeffrey Williams**
IBA@intentbound.com
IntentBound.com
Patent GB2603013.0 Pending · WIPO DAS C9A6 · IETF draft-williams-intent-token-00
