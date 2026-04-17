# guard.py - IBA Intent Bound Authorization · Digital Worker Guard
# Patent GB2603013.0 (Pending) · UK IPO · Filed February 5, 2026
# WIPO DAS Confirmed April 15, 2026 · Access Code C9A6
# IETF draft-williams-intent-token-00 · intentbound.com
#
# Govern your digital worker. Human intent declared before the first model fires.
# Works with Perplexity, Claude Code, custom multi-model stacks,
# and any long-running or parallel agent system.

import json
import yaml
import os
import time
import argparse
from datetime import datetime, timezone


class IBABlockedError(Exception):
    """Raised when a digital worker action is blocked by the IBA gate."""
    pass


class IBATerminatedError(Exception):
    """Raised when the digital worker session is terminated by the IBA gate."""
    pass


HOLLOW_LEVELS = {
    "light":  ["purchase", "payment", "credential"],
    "medium": ["purchase", "payment", "credential", "external_email",
               "file_delete", "calendar_write", "social_post"],
    "deep":   ["purchase", "payment", "credential", "external_email",
               "file_delete", "calendar_write", "social_post",
               "contact_access", "financial", "banking", "uncertified_model"],
}


class IBADigitalWorkerGuard:
    """
    IBA enforcement layer for multi-model digital workers.
    Reads .iba.yaml, validates every model invocation and tool call
    against declared scope, enforces model limits, API call caps,
    runtime limits, and terminates on kill threshold.
    Writes immutable audit chain to worker-audit.jsonl.

    Compatible with Perplexity, Claude Code, custom multi-model stacks,
    and any long-running or parallel agent system.
    """

    def __init__(self, config_path=".iba.yaml", audit_path="worker-audit.jsonl"):
        self.config_path = config_path
        self.audit_path = audit_path
        self.terminated = False
        self.session_id = f"worker-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        self.action_count = 0
        self.block_count = 0
        self.model_calls = {}
        self.api_calls = 0
        self.session_start = datetime.now(timezone.utc)

        self.config = self._load_config()
        self.scope           = [s.lower() for s in self.config.get("scope", [])]
        self.denied          = [d.lower() for d in self.config.get("denied", [])]
        self.default_posture = self.config.get("default_posture", "DENY_ALL")
        self.kill_threshold  = self.config.get("kill_threshold", None)
        self.hard_expiry     = self.config.get("temporal_scope", {}).get("hard_expiry", None)
        self.runtime_limits  = self.config.get("runtime_limits", {})
        self.model_limits    = self.config.get("model_limits", {})
        self.max_api_calls   = self.runtime_limits.get("max_api_calls", None)
        self.max_hours       = self.runtime_limits.get("max_session_hours", None)
        self.permitted_models = [m.lower() for m in
                                  self.model_limits.get("permitted_models", [])]
        self.forbidden_models = [m.lower() for m in
                                  self.model_limits.get("forbidden_models", [])]

        self._log_event("SESSION_START", "IBA Digital Worker Guard initialised", "ALLOW")
        self._print_header()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            print(f"⚠️  No {self.config_path} found — creating default DENY_ALL config")
            default = {
                "intent": {"description": "No digital worker intent declared — DENY_ALL posture active"},
                "scope": [], "denied": [], "default_posture": "DENY_ALL",
            }
            with open(self.config_path, "w") as f:
                yaml.dump(default, f)
            return default
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def _print_header(self):
        intent = self.config.get("intent", {})
        desc = intent.get("description", "No intent declared") if isinstance(intent, dict) else str(intent)
        print("\n" + "═" * 66)
        print("  IBA DIGITAL WORKER GUARD · Intent Bound Authorization")
        print("  Patent GB2603013.0 Pending · WIPO DAS C9A6 · intentbound.com")
        print("═" * 66)
        print(f"  Session   : {self.session_id}")
        print(f"  Intent    : {desc[:58]}...")
        print(f"  Posture   : {self.default_posture}")
        print(f"  Scope     : {', '.join(self.scope) if self.scope else 'NONE'}")
        print(f"  Denied    : {', '.join(self.denied) if self.denied else 'NONE'}")
        if self.permitted_models:
            print(f"  Models    : {', '.join(self.permitted_models)}")
        if self.max_api_calls:
            print(f"  API limit : {self.max_api_calls} calls")
        if self.max_hours:
            print(f"  Runtime   : {self.max_hours}h max")
        if self.hard_expiry:
            print(f"  Expires   : {self.hard_expiry}")
        if self.kill_threshold:
            print(f"  Kill      : {self.kill_threshold}")
        print("═" * 66 + "\n")

    def _is_expired(self):
        if not self.hard_expiry:
            return False
        try:
            expiry = datetime.fromisoformat(str(self.hard_expiry))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) > expiry
        except Exception:
            return False

    def _is_runtime_exceeded(self):
        if not self.max_hours:
            return False
        elapsed = (datetime.now(timezone.utc) - self.session_start).total_seconds() / 3600
        return elapsed > self.max_hours

    def _match_scope(self, action: str) -> bool:
        return any(s in action.lower() for s in self.scope)

    def _match_denied(self, action: str) -> bool:
        return any(d in action.lower() for d in self.denied)

    def _match_kill_threshold(self, action: str) -> bool:
        if not self.kill_threshold:
            return False
        thresholds = [t.strip().lower() for t in str(self.kill_threshold).split("|")]
        return any(t in action.lower() for t in thresholds)

    def _log_event(self, event_type: str, action: str, verdict: str, reason: str = ""):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "event_type": event_type,
            "action": action[:200],
            "verdict": verdict,
            "reason": reason,
            "api_calls": self.api_calls,
        }
        with open(self.audit_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def check_action(self, action: str, model: str = None) -> bool:
        """
        Gate check. Call before every model invocation or tool call.
        Returns True if permitted.
        Raises IBABlockedError if blocked.
        Raises IBATerminatedError if kill threshold triggered.
        """
        if self.terminated:
            raise IBATerminatedError("Digital worker session terminated. No further actions permitted.")

        self.action_count += 1
        self.api_calls += 1
        start = time.perf_counter()

        # 1. Expiry
        if self._is_expired():
            self._log_event("BLOCK", action, "BLOCK", "Certificate expired")
            self.block_count += 1
            print(f"  ✗ BLOCKED  [{action[:64]}]\n    → Certificate expired")
            raise IBABlockedError(f"Certificate expired: {action}")

        # 2. Runtime limit
        if self._is_runtime_exceeded():
            self._log_event("BLOCK", action, "BLOCK", f"Session runtime exceeded {self.max_hours}h")
            self.block_count += 1
            print(f"  ✗ BLOCKED  [{action[:64]}]\n    → Runtime limit exceeded ({self.max_hours}h)")
            raise IBABlockedError(f"Runtime limit: {action}")

        # 3. API call limit
        if self.max_api_calls and self.api_calls > self.max_api_calls:
            self._log_event("BLOCK", action, "BLOCK", f"API call limit reached: {self.api_calls}/{self.max_api_calls}")
            self.block_count += 1
            print(f"  ✗ BLOCKED  [{action[:64]}]\n    → API call limit reached ({self.api_calls}/{self.max_api_calls})")
            raise IBABlockedError(f"API limit: {action}")

        # 4. Model check
        if model:
            model_lower = model.lower()
            if self.forbidden_models and any(f in model_lower for f in self.forbidden_models):
                self._log_event("BLOCK", action, "BLOCK", f"Forbidden model: {model}")
                self.block_count += 1
                print(f"  ✗ BLOCKED  [{action[:64]}]\n    → Forbidden model: {model}")
                raise IBABlockedError(f"Forbidden model {model}: {action}")
            if self.permitted_models and not any(p in model_lower for p in self.permitted_models):
                self._log_event("BLOCK", action, "BLOCK", f"Model not in permitted list: {model}")
                self.block_count += 1
                print(f"  ✗ BLOCKED  [{action[:64]}]\n    → Model not permitted: {model}")
                raise IBABlockedError(f"Unpermitted model {model}: {action}")
            self.model_calls[model] = self.model_calls.get(model, 0) + 1

        # 5. Kill threshold
        if self._match_kill_threshold(action):
            self._log_event("TERMINATE", action, "TERMINATE", "Kill threshold triggered")
            self.terminated = True
            print(f"  ✗ TERMINATE [{action[:62]}]\n    → Kill threshold — worker session ended")
            self._log_event("SESSION_END", "Kill threshold", "TERMINATE")
            raise IBATerminatedError(f"Kill threshold triggered: {action}")

        # 6. Denied list
        if self._match_denied(action):
            self._log_event("BLOCK", action, "BLOCK", "Action in denied list")
            self.block_count += 1
            print(f"  ✗ BLOCKED  [{action[:64]}]\n    → Action in denied list")
            raise IBABlockedError(f"Denied: {action}")

        # 7. Scope
        if self.scope and not self._match_scope(action):
            if self.default_posture == "DENY_ALL":
                self._log_event("BLOCK", action, "BLOCK", "Outside declared worker scope — DENY_ALL")
                self.block_count += 1
                print(f"  ✗ BLOCKED  [{action[:64]}]\n    → Outside declared worker scope (DENY_ALL)")
                raise IBABlockedError(f"Out of scope: {action}")

        # 8. ALLOW
        elapsed_ms = (time.perf_counter() - start) * 1000
        model_str = f" [{model}]" if model else ""
        self._log_event("ALLOW", action, "ALLOW", f"Within worker scope ({elapsed_ms:.3f}ms)")
        print(f"  ✓ ALLOWED  [{action[:56]}]{model_str}  ({elapsed_ms:.3f}ms)")
        return True

    def hollow(self, task: str, level: str = "medium") -> str:
        """Redact high-risk actions from the task description before worker activation."""
        blocked = HOLLOW_LEVELS.get(level, HOLLOW_LEVELS["medium"])
        hollowed = task
        redacted = []
        for item in blocked:
            if item.lower() in task.lower():
                hollowed = hollowed.replace(item, f"[REDACTED:{item.upper()}]")
                redacted.append(item)
        if redacted:
            print(f"  ◎ HOLLOWED [{level}] — blocked: {', '.join(redacted)}")
            self._log_event("HOLLOW", f"Task hollowing: {level}", "ALLOW",
                           f"Blocked: {', '.join(redacted)}")
        return hollowed

    def summary(self):
        print("\n" + "═" * 66)
        print("  IBA DIGITAL WORKER GUARD · SESSION SUMMARY")
        print("═" * 66)
        print(f"  Session    : {self.session_id}")
        print(f"  Actions    : {self.action_count}")
        print(f"  Blocked    : {self.block_count}")
        print(f"  Allowed    : {self.action_count - self.block_count}")
        print(f"  API calls  : {self.api_calls}")
        if self.model_calls:
            print(f"  Models     : {dict(self.model_calls)}")
        print(f"  Status     : {'TERMINATED' if self.terminated else 'COMPLETE'}")
        print(f"  Audit log  : {self.audit_path}")
        print("═" * 66 + "\n")

    def print_audit_log(self):
        print("\n── WORKER AUDIT CHAIN ───────────────────────────────────────────")
        if not os.path.exists(self.audit_path):
            print("  No audit log found.")
            return
        with open(self.audit_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    verdict = entry['verdict']
                    symbol = "✓" if verdict == "ALLOW" else "✗"
                    print(f"  {symbol} {entry['timestamp'][:19]}  {verdict:<10}  {entry['action'][:50]}")
                except Exception:
                    pass
        print("─────────────────────────────────────────────────────────────────\n")


# ── CLI & Demonstration ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='IBA Digital Worker Guard')
    parser.add_argument('task', nargs='?', help='Digital worker task description')
    parser.add_argument('--hollow', choices=['light', 'medium', 'deep'],
                        default=None, help='Apply safe hollowing to task')
    parser.add_argument('--config', default='.iba.yaml')
    parser.add_argument('--demo', action='store_true', help='Run demonstration')
    args = parser.parse_args()

    guard = IBADigitalWorkerGuard(config_path=args.config)

    if args.task and args.hollow:
        task = guard.hollow(args.task, args.hollow)
        print(f"\n  Task (hollowed): {task}\n")

    if args.demo or not args.task:
        scenarios = [
            # ALLOW — within scope with permitted models
            ("Research competitor pricing across web sources",      "claude_opus"),
            ("Analyse market report — summarise key findings",      "gemini_pro"),
            ("Draft internal competitor analysis report",           "claude_opus"),
            ("Web search for industry pricing data",                "grok"),

            # BLOCK — denied list
            ("Post summary to LinkedIn and Twitter",                "claude_opus"),
            ("Access contact list for outreach campaign",          "gemini_pro"),
            ("Send external email to competitor contact",           "grok"),

            # BLOCK — unpermitted model
            ("Generate images for presentation",                    "nano_banana_pro"),

            # TERMINATE — kill threshold
            ("Purchase premium data subscription for research",     "claude_opus"),
        ]

        print("── Running Digital Worker Gate Checks ───────────────────────────\n")

        for action, model in scenarios:
            try:
                guard.check_action(action, model=model)
            except IBATerminatedError as e:
                print(f"\n  WORKER SESSION TERMINATED: {e}")
                break
            except IBABlockedError:
                pass

    guard.summary()
    guard.print_audit_log()


if __name__ == "__main__":
    main()
