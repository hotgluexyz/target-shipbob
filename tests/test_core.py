"""Tests standard target features using the built-in SDK tests library."""

from __future__ import annotations

from typing import Any

from hotglue_singer_sdk.testing import get_standard_target_tests

from target_shipbob.target import TargetShipbob

SAMPLE_CONFIG: dict[str, Any] = {
    "access_token": "test-access-token",
}


def test_standard_target_tests() -> None:
    """Run standard target tests from the SDK."""
    tests = get_standard_target_tests(
        TargetShipbob,
        config=SAMPLE_CONFIG,
    )
    for test in tests:
        test()


def test_target_about() -> None:
    """Target instantiates and prints about with required config."""
    target = TargetShipbob(config=SAMPLE_CONFIG)
    assert target.name == "target-shipbob"
    assert {s.name for s in target.SINK_TYPES} == {"Items", "SalesOrder"}
