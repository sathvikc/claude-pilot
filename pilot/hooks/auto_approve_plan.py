#!/usr/bin/env python3
"""PermissionRequest hook for ExitPlanMode: skip the dialog + request bypassPermissions restore.

In the /spec workflow ExitPlanMode is purely a model-switch lever (Opus -> Sonnet),
NOT the plan-approval mechanism. The real approval is a separate AskUserQuestion gate
(spec-plan/steps/12-approval.md). The decision message therefore must NEVER say
"approved": earlier wording ("Plan auto-approved") was parroted by agents as
"Plan approved", causing them to skip the approval gate and start implementing.

Two upstream issues limit effectiveness on current CC builds:
  #49525 - updatedPermissions setMode:bypassPermissions silently dropped on CC 2.1.110+
  #39973 - ExitPlanMode resets session to acceptEdits regardless of prior mode
Both are self-fixing once Anthropic ships patches. The behavior:allow part (skip dialog) works now.
"""

import json
import sys

print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": "allow",
                    "updatedPermissions": [
                        {
                            "type": "setMode",
                            "mode": "bypassPermissions",
                            "destination": "session",
                        }
                    ],
                    "message": "ExitPlanMode allowed (model switch); restoring bypassPermissions - permission action only, NOT plan approval",
                },
            }
        }
    )
)
sys.exit(0)
