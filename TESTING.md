# Testing iba-digital-worker-guard

No terminal required. Test in your browser in 3 minutes using Google Colab.

---

## Browser Test — Google Colab

**Step 1** — Open [colab.research.google.com](https://colab.research.google.com) · New notebook

**Step 2** — Run Cell 1:
```python
!pip install pyyaml
```

**Step 3** — Run Cell 2 — create the digital worker certificate:
```python
iba_yaml = """
intent:
  description: "Research competitor pricing and draft internal report. No purchases. No external email. No social posting."

scope:
  - research
  - web_search
  - search
  - read
  - draft
  - report
  - internal
  - summarise
  - analyse
  - market
  - pricing
  - competitor

denied:
  - post
  - social
  - linkedin
  - twitter
  - contact_list
  - external_email
  - external email
  - send email
  - file_delete
  - calendar_write
  - credential
  - banking

default_posture: DENY_ALL

kill_threshold: "purchase | payment | send_email_external | file_delete | credential_access | financial_transaction"

model_limits:
  permitted_models:
    - claude_opus
    - gemini_pro
    - grok
  forbidden_models:
    - nano_banana_pro
    - uncertified

runtime_limits:
  max_session_hours: 8
  max_api_calls: 1000

temporal_scope:
  hard_expiry: "2026-12-31"
"""

with open(".iba.yaml", "w") as f:
    f.write(iba_yaml)

print("Digital worker certificate written.")
```

**Step 4** — Run Cell 3 — run the guard:
```python
import json, yaml, os, time
from datetime import datetime, timezone

class IBABlockedError(Exception): pass
class IBATerminatedError(Exception): pass

class IBADigitalWorkerGuard:
    def __init__(self):
        self.terminated = False
        self.action_count = 0
        self.block_count = 0
        self.api_calls = 0
        self.model_calls = {}
        self.session_id = f"worker-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        with open(".iba.yaml") as f:
            cfg = yaml.safe_load(f)
        self.scope = [s.lower() for s in cfg.get("scope", [])]
        self.denied = [d.lower() for d in cfg.get("denied", [])]
        self.kill_threshold = [t.strip().lower() for t in str(cfg.get("kill_threshold","")).split("|")]
        self.default_posture = cfg.get("default_posture", "DENY_ALL")
        ml = cfg.get("model_limits", {})
        self.permitted_models = [m.lower() for m in ml.get("permitted_models", [])]
        self.forbidden_models = [m.lower() for m in ml.get("forbidden_models", [])]
        rl = cfg.get("runtime_limits", {})
        self.max_api_calls = rl.get("max_api_calls")
        print(f"✅ IBA Digital Worker Guard loaded · Session: {self.session_id}")
        print(f"   Scope   : {', '.join(self.scope)}")
        print(f"   Denied  : {', '.join(self.denied)}")
        print(f"   Models  : {', '.join(self.permitted_models)}\n")

    def check_action(self, action, model=None):
        if self.terminated:
            raise IBATerminatedError("Worker session terminated.")
        self.action_count += 1
        self.api_calls += 1
        a = action.lower()

        if self.max_api_calls and self.api_calls > self.max_api_calls:
            self.block_count += 1
            print(f"  ✗ BLOCKED   [{action}]\n    → API call limit reached")
            raise IBABlockedError(f"API limit: {action}")

        if model:
            ml = model.lower()
            if self.forbidden_models and any(f in ml for f in self.forbidden_models):
                self.block_count += 1
                print(f"  ✗ BLOCKED   [{action}]\n    → Forbidden model: {model}")
                raise IBABlockedError(f"Forbidden model: {action}")
            if self.permitted_models and not any(p in ml for p in self.permitted_models):
                self.block_count += 1
                print(f"  ✗ BLOCKED   [{action}]\n    → Model not permitted: {model}")
                raise IBABlockedError(f"Unpermitted model: {action}")
            self.model_calls[model] = self.model_calls.get(model, 0) + 1

        if any(k in a for k in self.kill_threshold if k):
            self.terminated = True
            print(f"  ✗ TERMINATE [{action}]\n    → Kill threshold — worker session ended")
            raise IBATerminatedError(f"Kill threshold: {action}")

        if any(d in a for d in self.denied if d):
            self.block_count += 1
            print(f"  ✗ BLOCKED   [{action}]\n    → Action in denied list")
            raise IBABlockedError(f"Denied: {action}")

        if self.scope and not any(s in a for s in self.scope):
            if self.default_posture == "DENY_ALL":
                self.block_count += 1
                print(f"  ✗ BLOCKED   [{action}]\n    → Outside declared worker scope (DENY_ALL)")
                raise IBABlockedError(f"Out of scope: {action}")

        model_str = f" [{model}]" if model else ""
        print(f"  ✓ ALLOWED   [{action}]{model_str}")
        return True

guard = IBADigitalWorkerGuard()

scenarios = [
    ("Research competitor pricing across web sources",    "claude_opus"),
    ("Analyse market report — summarise key findings",    "gemini_pro"),
    ("Draft internal competitor analysis report",         "claude_opus"),
    ("Web search for industry pricing data",              "grok"),
    ("Post summary to LinkedIn and Twitter",              "claude_opus"),
    ("Send external email to competitor contact",         "grok"),
    ("Generate images for presentation",                  "nano_banana_pro"),
    ("Purchase premium data subscription for research",   "claude_opus"),
]

for action, model in scenarios:
    try:
        guard.check_action(action, model=model)
    except IBATerminatedError:
        break
    except IBABlockedError:
        pass

print(f"\n{'═'*60}")
print(f"  Actions: {guard.action_count} · Blocked: {guard.block_count} · API calls: {guard.api_calls}")
print(f"  Models : {guard.model_calls}")
print(f"  Status : {'TERMINATED' if guard.terminated else 'COMPLETE'}")
print(f"{'═'*60}")
```

---

## Expected Output

```
✅ IBA Digital Worker Guard loaded · Session: worker-...

  ✓ ALLOWED   [Research competitor pricing across web sources] [claude_opus]
  ✓ ALLOWED   [Analyse market report — summarise key findings] [gemini_pro]
  ✓ ALLOWED   [Draft internal competitor analysis report] [claude_opus]
  ✓ ALLOWED   [Web search for industry pricing data] [grok]
  ✗ BLOCKED   [Post summary to LinkedIn and Twitter]
    → Action in denied list
  ✗ BLOCKED   [Send external email to competitor contact]
    → Action in denied list
  ✗ BLOCKED   [Generate images for presentation]
    → Forbidden model: nano_banana_pro
  ✗ TERMINATE [Purchase premium data subscription for research]
    → Kill threshold — worker session ended

════════════════════════════════════════════════════════════
  Actions: 8 · Blocked: 3 · API calls: 8
  Models : {'claude_opus': 3, 'gemini_pro': 1, 'grok': 1}
  Status : TERMINATED
════════════════════════════════════════════════════════════
```

---

## With Safe Hollowing

```bash
# Redact high-risk actions from task before worker activation
python guard.py "research competitors and send report to external partners" --hollow medium
```

---

## Local Test

```bash
git clone https://github.com/Grokipaedia/iba-digital-worker-guard.git
cd iba-digital-worker-guard
pip install -r requirements.txt
python guard.py --demo
```

---

## Live Demo

**governinglayer.com/governor-html/**

Edit the cert. Run any digital worker action. See the gate fire.

---

IBA Intent Bound Authorization · Patent GB2603013.0 Pending · WIPO DAS C9A6
IBA@intentbound.com · IntentBound.com
