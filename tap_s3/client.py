"""Custom client handling, including S3Stream base class."""

from __future__ import annotations

from typing import Any, Iterable

from singer_sdk import typing as th
from singer_sdk.streams import Stream

from tap_s3.s3 import S3


class S3Stream(Stream):
    """Stream class for S3 streams."""

    name = "hello_stream"
    columns: list[str] = ["column1", "column2"]  # noqa: RUF012
    s3_client: S3
    columns: list[str] = []

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        """Init CSVStram."""
        # cache file_config so we dont need to go iterating the config list again later
        super().__init__(*args, **kwargs)

    def get_records(
        self,
        context: dict | None,  # noqa: ARG002
    ) -> Iterable[dict]:
        """Return a generator of record-type dictionary objects.

        The optional `context` argument is used to identify a specific slice of the
        stream if partitioning is required for the stream. Most implementations do not
        require partitioning and should ignore the `context` argument.

        Args:
            context: Stream partition or context dictionary.

        Raises:
            NotImplementedError: If the implementation is TODO
        """
        self.s3_client = S3(self.config)
        for record in self.s3_client.get_records_from_files(self.config):
            self.logger.info(record)
            yield record

    def get_records_from_files(self) -> list[Any]:
        """Get records from files.

        Returns:
            list[Any]: List of records
        """
        return [
            {"column1": "value1", "column2": "value2"},
            {"column1": "value3", "column2": "value4"},
            {"column1": "value5", "column2": "value6"},
        ]

    @property
    def schema(self) -> dict:
        """Return dictionary of record schema.

        Dynamically detect the json schema for the stream.
        This is evaluated prior to any records being retrieved.
        """
        properties: list[th.Property] = []
        self.primary_keys = ["column1"]
        self.s3_client = S3(self.config)

        columns = self.columns or next(
            self.s3_client.get_records_from_files(self.config),
        )
        for column, value in columns.items():
            if isinstance(value, bool):
                properties.append(th.Property(column, th.BooleanType()))
            elif isinstance(value, int):
                properties.append(th.Property(column, th.IntegerType()))
            elif isinstance(value, float):
                properties.append(th.Property(column, th.NumberType()))
            else:
                # Set all types to string
                properties.append(th.Property(column, th.StringType()))  # noqa: PERF401

        self.columns = columns

        return th.PropertiesList(*properties).to_dict()
