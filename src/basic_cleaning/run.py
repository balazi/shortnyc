#!/usr/bin/env python
"""Download a W&B artifact, perform basic cleaning, and log the result."""

import argparse
import logging

import pandas as pd
import wandb


logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")
logger = logging.getLogger()


def go(args):
    run = wandb.init(job_type="basic_cleaning")
    run.config.update(args)

    logger.info("Loading input artifact %s", args.input_artifact)
    artifact_local_path = run.use_artifact(args.input_artifact).file()
    df = pd.read_csv(artifact_local_path)

    logger.info("Filtering prices outside [%s, %s]", args.min_price, args.max_price)
    df = df[df["price"].between(args.min_price, args.max_price)].copy()

    logger.info("Converting last_review to datetime")
    df["last_review"] = pd.to_datetime(df["last_review"])

    logger.info("Filtering properties outside NYC coordinate boundaries")
    in_nyc = df["longitude"].between(-74.25, -73.50) & df["latitude"].between(40.5, 41.2)
    df = df[in_nyc].copy()

    logger.info("Saving and uploading cleaned dataset")
    df.to_csv("clean_sample.csv", index=False)
    artifact = wandb.Artifact(
        args.output_artifact,
        type=args.output_type,
        description=args.output_description,
    )
    artifact.add_file("clean_sample.csv")
    run.log_artifact(artifact)
    artifact.wait()
    run.finish()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform basic data cleaning")

    parser.add_argument(
        "--input_artifact",
        type=str,
        help="W&B artifact containing the raw CSV dataset",
        required=True,
    )
    parser.add_argument(
        "--output_artifact",
        type=str,
        help="Name of the cleaned W&B artifact",
        required=True,
    )
    parser.add_argument(
        "--output_type",
        type=str,
        help="W&B artifact type for the cleaned dataset",
        required=True,
    )
    parser.add_argument(
        "--output_description",
        type=str,
        help="Description of the cleaned dataset artifact",
        required=True,
    )
    parser.add_argument(
        "--min_price",
        type=float,
        help="Minimum inclusive nightly price to retain",
        required=True,
    )
    parser.add_argument(
        "--max_price",
        type=float,
        help="Maximum inclusive nightly price to retain",
        required=True,
    )

    args = parser.parse_args()
    go(args)
