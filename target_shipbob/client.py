"""HTTP client and sink base classes for Shipbob."""

from __future__ import annotations

from typing import Any

import requests
from hotglue_etl_exceptions import InvalidCredentialsError
from hotglue_singer_sdk.exceptions import FatalAPIError
from hotglue_singer_sdk.target_sdk.auth import BearerTokenAuthenticator
from hotglue_singer_sdk.target_sdk.client import HotglueBaseSink, HotglueBatchSink, HotglueSink

HTTP_OK = 200
HTTP_UNPROCESSABLE = 422


class ShipbobAuthenticator(BearerTokenAuthenticator):
    """Bearer auth using ``access_token`` (same config key as the previous target)."""

    @property
    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._config['access_token']}"}


class ShipbobSink(HotglueBaseSink):
    """Shipbob base target sink class."""

    _channel_id: str | None = None

    @property
    def base_url(self) -> str:
        if self.config.get("sandbox"):
            return "https://sandbox-api.shipbob.com/2026-07"
        return "https://api.shipbob.com/2026-07"

    @property
    def authenticator(self) -> Any:
        return ShipbobAuthenticator(self._target)

    @property
    def channel_id(self) -> str:
        if ShipbobSink._channel_id is not None:
            return ShipbobSink._channel_id

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.config['access_token']}",
        }
        response = requests.get(
            f"{self.base_url}/channel",
            headers=headers,
            timeout=self.timeout,
        )
        if response.status_code != HTTP_OK:
            msg = f"Failed to request default channel: {response.text}"
            raise FatalAPIError(msg)

        channels = response.json()["items"]
        write_channel = next(
            (
                channel
                for channel in channels
                if "orders_write" in (channel.get("scopes") or [])
            ),
            None,
        )
        if write_channel is None:
            msg = "No Shipbob channel with orders_write scope found"
            raise FatalAPIError(msg)

        ShipbobSink._channel_id = str(write_channel["id"])
        return ShipbobSink._channel_id

    @property
    def http_headers(self) -> dict:
        return {"shipbob_channel_id": self.channel_id}

    def validate_response(self, response: requests.Response) -> None:
        if response.status_code == HTTP_UNPROCESSABLE:
            return
        if response.status_code in (401, 403):
            raise InvalidCredentialsError(response.text)
        super().validate_response(response)


class ShipbobRecordSink(ShipbobSink, HotglueSink):
    """Shipbob record sink base class."""

    name = "ShipbobRecordSink"

    def preprocess_record(self, record: dict, _context: dict) -> dict:
        return record

    def upsert_record(self, record: dict, _context: dict) -> tuple[Any, bool, dict]:
        response = self.request_api("POST", request_data=record)
        return response.json().get("id"), True, {}


class ShipbobBatchSink(ShipbobSink, HotglueBatchSink):
    """Shipbob batch sink base class."""

    name = "ShipbobBatchSink"

    def process_batch_record(self, record: dict, _index: int) -> dict:
        return record

    def make_batch_request(self, records: list[dict]) -> Any:
        return self.request_api("POST", request_data=records)

    def handle_batch_response(self, _response: Any) -> dict:
        return {"state_updates": []}
