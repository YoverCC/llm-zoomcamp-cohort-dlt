import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
import dlt
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources

load_dotenv()


@dlt.source(name="logfire")
def logfire_source(access_token: Optional[str] = dlt.secrets.value):
    """Define Logfire REST API resources for dlt."""
    if not access_token:
        access_token = os.environ.get("LOGFIRE_READ_TOKEN")
        print(f"Using LOGFIRE_READ_TOKEN from environment: {access_token}")
    if not access_token:
        access_token = os.environ.get("LOGFIRE_TOKEN")
        print(f"Using LOGFIRE_TOKEN from environment: {access_token}")
    if not access_token:
        raise ValueError(
            "Set LOGFIRE_READ_TOKEN, LOGFIRE_TOKEN, or configure access_token in .dlt/secrets.toml"
        )

    base_url = os.environ.get("LOGFIRE_BASE_URL", "https://logfire-us.pydantic.dev")
    print(f"Using LOGFIRE_BASE_URL from environment: {base_url}")

    query_sql = os.environ.get(
        "LOGFIRE_QUERY_SQL",
        "SELECT * FROM records_all LIMIT 100",
    )
    query_days = int(os.environ.get("LOGFIRE_QUERY_MIN_DAYS", "7"))
    min_timestamp = (
        datetime.now(timezone.utc) - timedelta(days=query_days)
    ).isoformat()

    config: RESTAPIConfig = {
        "client": {
            "base_url": base_url,
            "auth": {"type": "bearer", "token": access_token},
        },
        "resource_defaults": {
            "write_disposition": "append",
        },
        "resources": [
            {
                "name": "query",
                "endpoint": {
                    "path": "v2/query",
                    "method": "POST",
                    "json": {
                        "sql": query_sql,
                        "min_timestamp": min_timestamp,
                        "include_schema": True,
                    },
                    "paginator": "single_page",
                    "data_selector": "data",
                },
            },
            {
                "name": "users",
                "endpoint": {"path": "users"},
            },
        ],
    }

    yield from rest_api_resources(config)


def load_logfire_data() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="logfire_pipeline",
        destination="duckdb",
        dataset_name="logfire_data",
    )
    load_info = pipeline.run(logfire_source())
    print(load_info)


if __name__ == "__main__":
    load_logfire_data()
