"""Shipbob target class."""

from __future__ import annotations

from hotglue_singer_sdk import typing as th
from hotglue_singer_sdk.target_sdk.target import TargetHotglue
from target_shipbob.sinks import ItemsSink, SalesOrderSink


class TargetShipbob(TargetHotglue):
    """Target for Shipbob."""

    name = "target-shipbob"
    SINK_TYPES = [ItemsSink, SalesOrderSink]

    config_jsonschema = th.PropertiesList(
        th.Property(
            "access_token",
            th.StringType,
            required=True,
            description="Shipbob Personal Access Token used as a Bearer token",
        ),
        th.Property(
            "sandbox",
            th.BooleanType,
            description="Use the Shipbob sandbox API (sandbox-api.shipbob.com/2026-07)",
            default=False,
        ),
    ).to_dict()


if __name__ == "__main__":
    TargetShipbob.cli()
