import asyncio

from app.computer_control import MacComputerController, plan_from_consensus
from app.schemas import ActionType, AnalysisResult, ComputerAction, Severity


def consensus() -> AnalysisResult:
    return AnalysisResult(
        summary="Database timeout",
        severity=Severity.warning,
        likely_causes=["Network"],
        recommended_actions=["Inspect system load"],
    )


def test_consensus_becomes_reviewable_action_plan() -> None:
    plan = plan_from_consensus(consensus())
    assert plan.requires_approval is True
    assert [action.type for action in plan.actions] == [
        ActionType.notify,
        ActionType.open_app,
    ]


def test_execution_requires_explicit_approval() -> None:
    controller = MacComputerController(True, {"Activity Monitor"})
    action = ComputerAction(
        type=ActionType.open_app,
        target="Activity Monitor",
        reason="Inspect load",
    )
    response = asyncio.run(controller.execute(action, approved=False))
    assert response.status == "approval_required"


def test_controller_blocks_non_allowlisted_app() -> None:
    controller = MacComputerController(True, {"Activity Monitor"})
    action = ComputerAction(
        type=ActionType.open_app,
        target="Terminal",
        reason="Not allowed",
    )
    response = asyncio.run(controller.execute(action, approved=True))
    assert response.status == "blocked"


def test_controller_is_disabled_by_default() -> None:
    controller = MacComputerController(False, {"Activity Monitor"})
    action = ComputerAction(
        type=ActionType.notify,
        target="Hello",
        reason="Test",
    )
    response = asyncio.run(controller.execute(action, approved=True))
    assert response.status == "disabled"
