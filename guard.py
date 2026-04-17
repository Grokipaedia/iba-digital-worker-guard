# guard.py - IBA protection for digital workers / multi-model agents
import json
from datetime import datetime
import sys
import argparse

def create_iba_digital_worker_guard(task: str, hollow_level: str = None):
    cert = {
        "iba_version": "2.0",
        "certificate_id": f"digital-worker-guard-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "issued_at": datetime.now().isoformat(),
        "principal": "human-owner",
        "declared_intent": f"Run digital worker task: {task}. Multi-model, long-running operation under strict human intent only.",
        "scope_envelope": {
            "resources": ["research", "analysis", "task-execution"],
            "denied": ["unauthorized-deployment", "sensitive-data-exposure", "autonomous-financial-actions"],
            "default_posture": "DENY_ALL"
        },
        "temporal_scope": {
            "hard_expiry": (datetime.now().replace(year=datetime.now().year + 1)).isoformat()
        },
        "entropy_threshold": {
            "max_kl_divergence": 0.12,
            "flag_at": 0.08,
            "kill_at": 0.12
        },
        "iba_signature": "demo-signature"
    }

    protected_file = f"worker-task-{task.replace(' ', '-').lower()[:30]}.iba-protected.md"

    content = f"# Digital Worker Task: {task}\n\n[Task execution would occur here under IBA governance]\n\n<!-- IBA PROTECTED DIGITAL WORKER -->\n"

    if hollow_level:
        content += f"\n<!-- Hollowed ({hollow_level}): High-risk components protected by IBA certificate -->\n"

    with open(protected_file, "w", encoding="utf-8") as f:
        f.write("<!-- IBA PROTECTED DIGITAL WORKER -->\n")
        f.write(f"<!-- Intent Certificate: {json.dumps(cert, indent=2)} -->\n\n")
        f.write(content)

    print(f"✅ IBA-protected digital worker file created: {protected_file}")
    if hollow_level:
        print(f"   Hollowing level applied: {hollow_level}")
    else:
        print("   Full digital worker task protected by IBA certificate")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Governed digital worker with IBA")
    parser.add_argument("task", help="Description of the digital worker task")
    parser.add_argument("--hollow", choices=["light", "medium", "heavy"], help="Apply safe hollowing")
    args = parser.parse_args()

    create_iba_digital_worker_guard(args.task, args.hollow)
