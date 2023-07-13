import logging
import os
from typing import Dict, Generator, Optional

import boto3
import orjson

logger = logging.getLogger(__name__)


class S3:
    def __init__(
        self,
        config: Dict,
    ):
        """Initialize a default AWS session."""
        s3_config = {}
        aws_access_key_id = config.get("aws_access_key_id") or os.environ.get(
            "AWS_ACCESS_KEY_ID",
        )
        aws_secret_access_key = config.get("aws_secret_access_key") or os.environ.get(
            "AWS_SECRET_ACCESS_KEY",
        )
        aws_profile = config.get("aws_profile") or os.environ.get("AWS_PROFILE")

        self.bucket = config.get("s3_bucket")
        if aws_access_key_id and aws_secret_access_key:
            s3_config = {
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
            }
        else:
            s3_config = {
                "profile_name": aws_profile,
            }

        boto3.setup_default_session(**s3_config)
        self.client = boto3.client("s3")

    def get_records_from_files(self, config: Dict, sampled: bool = False) -> list[Dict]:
        for file in self.get_input_files(config["prefix"], sampled):
            for record in self.get_file(file["key"]).read().splitlines():
                yield orjson.loads(record)

    def get_input_files(self, prefix: str, sampled: bool) -> Generator:
        """Get input files from S3 bucket.

        Args:
            config (Dict): _description_
            modified_since (str, optional): _description_. Defaults to None.
        """

        for s3_object in sorted(
            self.list_files_in_bucket(prefix),
            key=lambda item: item["LastModified"],
            reverse=False,
        ):
            key = s3_object["Key"]
            last_modified = s3_object["LastModified"]
            if sampled:
                return {"key": key, "last_modified": last_modified}
            yield {"key": key, "last_modified": last_modified}

    def list_files_in_bucket(
        self,
        search_prefix: Optional[str] = None,
    ) -> Generator:
        """Gets all files in the given S3 bucket that match the search prefix
        :param bucket: S3 bucket name
        :param search_prefix: search pattern
        :param aws_endpoint_url: optional aws url
        :returns: generator containing all found files
        """  # noqa: D205, D415
        s3_object_count = 0

        max_results = 1000
        args = {
            "Bucket": self.bucket,
            "MaxKeys": max_results,
        }

        if search_prefix is not None:
            args["Prefix"] = search_prefix

        paginator = self.client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(**args)
        filtered_iterator = page_iterator.search("Contents[?Size > `0`][]")
        for obj in filtered_iterator:
            s3_object_count += 1
            yield obj

        if s3_object_count > 0:
            logger.info("Found %s files.", s3_object_count)
        else:
            logger.warning(
                'Found no files for bucket "%s" that match prefix "%s"',
                self.bucket,
                search_prefix,
            )

    def get_file(self, key: str) -> bytes:
        """Get file from S3.

        Args:
            key (str): _description_

        Returns:
            bytes: _description_
        """
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"]
