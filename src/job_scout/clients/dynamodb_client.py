"""Thin wrapper around the DynamoDB jobs table."""

from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

GSI_STATUS_CREATED_AT = "StatusCreatedAtIndex"


class DynamoDBClient:
    def __init__(self, table_name: str, region_name: str | None = None):
        resource = boto3.resource("dynamodb", region_name=region_name)
        self._table = resource.Table(table_name)

    def put_item(self, item: dict[str, Any]) -> None:
        self._table.put_item(Item=item)

    def update_item(self, job_id: str, updates: dict[str, Any]) -> None:
        expression_names = {f"#{k}": k for k in updates}
        expression_values = {f":{k}": v for k, v in updates.items()}
        update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
        self._table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
        )

    def get_item(self, job_id: str) -> dict[str, Any] | None:
        response = self._table.get_item(Key={"job_id": job_id})
        return response.get("Item")

    def query_by_status(
        self, status: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {
            "IndexName": GSI_STATUS_CREATED_AT,
            "KeyConditionExpression": Key("status").eq(status),
            "ScanIndexForward": False,
        }
        if limit is not None:
            kwargs["Limit"] = limit
        response = self._table.query(**kwargs)
        return response.get("Items", [])

    def scan_all(self, limit: int | None = None) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {}
        if limit is not None:
            kwargs["Limit"] = limit
        response = self._table.scan(**kwargs)
        return response.get("Items", [])
