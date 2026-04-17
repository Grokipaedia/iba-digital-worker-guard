# iba-digital-worker-guard

**Govern your digital worker. Human intent required.**

Perplexity just launched a full 24/7 digital worker that runs multiple models in parallel, handles long-running tasks, and works even while you sleep.

This tool adds real cryptographic governance.

Wrap any digital worker session with a signed **IBA Intent Certificate** so the agent can only act under your exact approved rules.

## Features
- Requires IBA-signed intent before any long-running or multi-model action
- Enforces scope, expiry, and behavioural limits across parallel models
- Optional safe hollowing / blocking of high-risk actions
- Works with any digital worker or multi-model agent system (Perplexity, Claude Code, custom stacks, etc.)

## Patent & Filings
- **Patent Pending**: GB2603013.0 (filed 5 Feb 2026, PCT route open — 150+ countries)
- **NIST Docket**: NIST-2025-0035 (13 IBA filings)
- **NCCoE Filings**: 10 submissions on AI agent authorization

## Quick Start
```bash
git clone https://github.com/Grokipaedia/iba-digital-worker-guard.git
cd iba-digital-worker-guard
pip install -r requirements.txt
python guard.py "your-digital-worker-task-description" --hollow medium
