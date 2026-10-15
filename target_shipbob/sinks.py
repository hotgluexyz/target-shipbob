"""Shipbob target sink class, which handles writing streams."""

from __future__ import annotations

from typing import Any

from target_shipbob.client import HTTP_UNPROCESSABLE, ShipbobRecordSink


class ItemsSink(ShipbobRecordSink):
    """Items (products) sink — POST ``/product``."""

    name = "Items"
    endpoint = "/product"

    def preprocess_record(self, record: dict, _context: dict) -> dict:
        name = record.get("name")
        sku = record.get("sku")
        return {
            "name": name,
            "variants": [{"sku": sku, "name": name}],
        }

    def upsert_record(self, record: dict, _context: dict) -> tuple[Any, bool, dict]:
        response = self.request_api("POST", request_data=record)
        if response.status_code == HTTP_UNPROCESSABLE:
            self.logger.info(
                "Skipping record %s with message: (%s) %s",
                record,
                response.status_code,
                response.json(),
            )
            return None, True, {"existing": True}

        return response.json().get("id"), True, {}


class SalesOrderSink(ShipbobRecordSink):
    """SalesOrder sink — POST ``/order``."""

    name = "SalesOrder"
    endpoint = "/order"

    def search_product(self, product_name: str) -> object:
        response = self.request_api(
            "GET",
            endpoint="/product",
            params={"Search": product_name},
        )
        items = response.json().get("items") or []
        if items:
            return items[0]["id"]
        return False

    def preprocess_record(self, record: dict, _context: dict) -> dict:
        shipping_address = record.get("shipping_address", {})
        payload = {
            "shipping_method": record.get("shipping_type", "Free 2-day Shipping"),
            "type": record.get("type", "DTC"),
            "recipient": {
                "name": record.get("customer_name"),
                "address": {
                    "address1": shipping_address.get("line1"),
                    "address2": shipping_address.get("line2"),
                    "city": shipping_address.get("city"),
                    "state": shipping_address.get("state"),
                    "country": shipping_address.get("country"),
                    "zip_code": shipping_address.get("postalCode"),
                },
                "email": record.get("customer_email"),
                "phone_number": record.get("billing_phone"),
            },
            "reference_id": record.get("order_number"),
            "order_number": record.get("order_number"),
            "purchase_date": record.get("transaction_date"),
            "financials": {"total_price": record.get("total_price")},
        }
        if record.get("location_id") is not None:
            payload["location_id"] = record["location_id"]

        products = []
        for line in record.get("line_items") or []:
            if line.get("id"):
                products.append({"id": line["id"], "quantity": line["quantity"]})
            elif line.get("sku") or line.get("reference_id"):
                product = {
                    "reference_id": line.get("reference_id") or line.get("sku"),
                    "quantity": line["quantity"],
                }
                if line.get("name") or line.get("product_name"):
                    product["name"] = line.get("name") or line.get("product_name")
                products.append(product)
            elif line.get("product_name"):
                product_id = self.search_product(line["product_name"])
                if product_id:
                    products.append({"id": product_id, "quantity": line["quantity"]})

        if not products:
            self.logger.warning("No products found in order, record: %s", record)

        payload["products"] = products
        return payload

    def upsert_record(self, record: dict, _context: dict) -> tuple[Any, bool, dict]:
        response = self.request_api("POST", request_data=record)
        if response.status_code == HTTP_UNPROCESSABLE:
            self.logger.info(
                "Skipping record %s with message: (%s) %s",
                record,
                response.status_code,
                response.json(),
            )
            return None, True, {"existing": True}

        return response.json().get("id"), True, {}
