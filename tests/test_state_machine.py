"""状态机测试。"""
import pytest

from app.core.exceptions import InvalidStateTransition
from app.engine.state_machine import can_transition, can_write_transition, transition


def test_valid_task_transitions():
    assert can_transition("pending", "parsing")
    assert can_transition("parsing", "reviewing")
    assert can_transition("parsing", "blocked")
    assert can_transition("reviewing", "done")
    assert can_transition("reviewing", "blocked")
    assert can_transition("blocked", "parsing")
    assert can_transition("blocked", "reviewing")


def test_invalid_task_transitions():
    assert not can_transition("pending", "done")
    assert not can_transition("done", "parsing")
    assert not can_transition("reviewing", "pending")


def test_transition_returns_target():
    assert transition("pending", "parsing") == "parsing"


def test_transition_raises_on_invalid():
    with pytest.raises(InvalidStateTransition):
        transition("done", "parsing")


def test_write_transitions():
    assert can_write_transition("not_written", "writing")
    assert can_write_transition("writing", "success")
    assert can_write_transition("writing", "failed")
    assert can_write_transition("failed", "writing")
    assert not can_write_transition("success", "writing")
