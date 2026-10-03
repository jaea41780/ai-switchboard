import asyncio
from urllib.parse import urlparse

from app.schemas import (
    ActionPlan,
    ActionType,
    AnalysisResult,
    ComputerAction,
    ExecuteActionResponse,
    Severity,
)


def plan_from_consensus(consensus: AnalysisResult) -> ActionPlan:
    """Convert a conclusion into reviewable, allowlisted computer actions."""
    actions = [
        ComputerAction(
            type=ActionType.notify,
            target=f"AI 결론: {consensus.summary}",
            reason="분석 결과를 사용자가 바로 확인할 수 있게 알립니다.",
        )
    ]
    if consensus.severity in (Severity.warning, Severity.critical):
        actions.append(
            ComputerAction(
                type=ActionType.open_app,
                target="Activity Monitor",
                reason="CPU, 메모리, 네트워크 상태를 사용자가 직접 확인합니다.",
            )
        )
    return ActionPlan(summary=consensus.summary, actions=actions)


class MacComputerController:
    def __init__(self, enabled: bool, allowed_apps: set[str]):
        self.enabled = enabled
        self.allowed_apps = allowed_apps

    async def execute(
        self, action: ComputerAction, approved: bool
    ) -> ExecuteActionResponse:
        if not approved:
            return ExecuteActionResponse(
                status="approval_required",
                message="Review the action and set approved=true to run it.",
            )
        if not self.enabled:
            return ExecuteActionResponse(
                status="disabled",
                message="Set ENABLE_COMPUTER_CONTROL=true on the local agent.",
            )

        if action.type == ActionType.open_app:
            if action.target not in self.allowed_apps:
                return ExecuteActionResponse(
                    status="blocked", message="App is not on the allowlist."
                )
            command = ["open", "-a", action.target]
        elif action.type == ActionType.open_url:
            parsed = urlparse(action.target)
            if parsed.scheme not in {"http", "https"}:
                return ExecuteActionResponse(
                    status="blocked", message="Only http/https URLs are allowed."
                )
            command = ["open", action.target]
        elif action.type == ActionType.notify:
            script = (
                "on run argv\n"
                "display notification (item 1 of argv) with title \"AI Switchboard\"\n"
                "end run"
            )
            command = ["osascript", "-e", script, action.target]
        else:
            return ExecuteActionResponse(
                status="blocked", message="Unsupported action type."
            )

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            return ExecuteActionResponse(
                status="failed", message=stderr.decode().strip() or "Action failed."
            )
        return ExecuteActionResponse(status="completed", message="Action completed.")
