"""S3 tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_s3 import client


class TapS3(Tap):
    """S3 tap class."""

    name = "tap-s3"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "s3_bucket",
            th.StringType,
            required=True,
            description="S3 bucket name",
        ),
        th.Property(
            "prefix",
            th.StringType,
            required=True,
            description="S3 bucket prefix",
        ),
        th.Property(
            "add_metadata_columns",
            th.BooleanType,
            required=False,
            default=True,
            description="S3 bucket prefix",
        ),
    ).to_dict()

    def discover_streams(self) -> list[client.S3Stream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            client.S3Stream(self),
        ]


if __name__ == "__main__":
    TapS3.cli()
