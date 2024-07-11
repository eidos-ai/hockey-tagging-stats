from dotenv import load_dotenv
import argparse
import logging
import os
import pandas as pd
import time
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import google
from typing import Any, List

load_dotenv()
import mongodb_connect
from utils import read_config
from tracks_dataclasses import TrackToTag, SubDataset


logger = logging.getLogger()
logger.handlers.clear()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


# Define the schema based on the TrackToTag class
TRACKS_SCHEMA = [
    bigquery.SchemaField("track_id", "STRING"),
    bigquery.SchemaField("game_id", "STRING"),
    bigquery.SchemaField("dataset_name", "STRING"),
    bigquery.SchemaField("detected_label", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("assigned_user", "STRING"),
    bigquery.SchemaField("assign_date", "TIMESTAMP"),
    bigquery.SchemaField("detection_model", "STRING"),
    bigquery.SchemaField("label_number", "STRING"),
    bigquery.SchemaField("referee", "BOOLEAN"),
    bigquery.SchemaField("wrong_track", "BOOLEAN"),
]

# Define the schema based on the SubDataset class
SUBDATASET_SCHEMA = [
    bigquery.SchemaField("dataset_name", "STRING"),
    bigquery.SchemaField("sub_dataset_name", "STRING"),
    bigquery.SchemaField("creation_time", "TIMESTAMP"),
    bigquery.SchemaField("number_of_tracks", "INTEGER"),
]


def create_table(
    bigquery_client: bigquery.Client,
    dataset_id: str,
    table_id: str,
    schema: list[bigquery.SchemaField],
) -> None:
    # Define table and dataset reference
    dataset_ref = bigquery_client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)
    # Check if the table already exists
    try:
        bigquery_client.get_table(table_ref)  # Make an API request.
        # If the table exists, delete it
        bigquery_client.delete_table(table_ref)
        logger.info(f"Table {table_id} in dataset {dataset_id} deleted.")
    except NotFound:
        pass  # If the table does not exist, do nothing.

    # Create a Table object with the schema
    table = bigquery.Table(table_ref, schema=schema)

    # Use the client to create the table in BigQuery
    created_table = bigquery_client.create_table(table)
    logger.info(
        f"Created table {created_table.project}.{created_table.dataset_id}.{created_table.table_id}"
    )


def wait_for_table(
    client: bigquery.Client, dataset_id: str, table_id: str, timeout: int = 300
) -> bool:
    """
    Waits for a table to exist and be in an active state.

    :param client: BigQuery Client
    :param dataset_id: ID of the dataset
    :param table_id: ID of the table
    :param timeout: Maximum time to wait (in seconds)
    :return: True if the table is found within the timeout, False otherwise
    """
    start_time = time.time()
    # time.sleep(20)
    while time.time() - start_time < timeout:
        try:
            client.get_table(f"{dataset_id}.{table_id}")  # Attempt to get the table
            return True
        except google.api_core.exceptions.NotFound:
            # Table not found, wait a bit before retrying
            time.sleep(10)

    (f"Timed out waiting for table {dataset_id}.{table_id}.")
    return False


def select_all_from_table(
    client: bigquery.Client, dataset_id: str, table_id: str
) -> Any:
    """
    Selects all records from a given BigQuery table.

    :param client: BigQuery Client
    :param dataset_id: ID of the dataset
    :param table_id: ID of the table
    :return: Result of the query
    """
    query = f"SELECT * FROM `{dataset_id}.{table_id}`"
    query_job = client.query(query)  # Start the query job

    return query_job.result()  # Wait for the job to complete and return the result


def truncate_table(client: bigquery.Client, dataset_id: str, table_id: str) -> None:
    """
    Truncates a specified BigQuery table (removes all data immediately).

    :param client: BigQuery Client
    :param dataset_id: ID of the dataset
    :param table_id: ID of the table
    """
    query = f"TRUNCATE TABLE `{dataset_id}.{table_id}`"
    query_job = client.query(query)  # Start the query job

    query_job.result()  # Wait for the job to complete

    logger.info(f"Table {dataset_id}.{table_id} truncated (all records deleted)")


# Function to convert TrackToTag objects to a Pandas DataFrame
def tracks_to_dataframe(tracks: List[TrackToTag]) -> pd.DataFrame:
    data = []
    for track in tracks:
        row = track.dict()
        data.append(row)
    return pd.DataFrame(data)


# Function to insert data into BigQuery using a load job
def insert_data_using_load_job(
    client: bigquery.Client,
    dataset_id: str,
    table_id: str,
    schema: list[bigquery.SchemaField],
    dataframe: pd.DataFrame,
) -> None:
    table_ref = client.dataset(dataset_id).table(table_id)

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_APPEND",
    )

    job = client.load_table_from_dataframe(dataframe, table_ref, job_config=job_config)
    job.result()  # Wait for the job to complete

    # Check for errors
    if not job.errors:
        logger.info(f"Successfully inserted {len(dataframe)} records.")
    else:
        logger.info(f"Failed to insert {len(job.errors)} records.")
        for error in job.errors:
            logger.info(f"Error: {error['message']}")


def export_data(
    table_id: str,
    dataset_id: str,
    schema: list[bigquery.SchemaField],
    data: list[TrackToTag] | list[SubDataset],
    bigquery_client: bigquery.Client,
) -> None:
    # Use this if tables have to be created again
    # create_table(bigquery_client, dataset_id, table_id, schema)

    truncate_table(bigquery_client, dataset_id, table_id)

    # Table takes some time to be enabled again.
    # Wait for the table
    if wait_for_table(bigquery_client, dataset_id, table_id):
        logger.info("Table is ready for operations.")
    else:
        logger.info("Table did not become active in time.")

    # Convert data to a Pandas DataFrame
    df = tracks_to_dataframe(data)

    # Insert data using a load job
    insert_data_using_load_job(bigquery_client, dataset_id, table_id, schema, df)


def export_to_bigquery() -> None:
    config = read_config()

    # Get Mongo TrackToTags, TaggedTracks and SubDatasets
    mongo_uri = config.get("MongoDB", "MONGO_URI", vars=os.environ)
    with mongodb_connect.MongoDBConnect(config["MongoDB"], mongo_uri) as mongodb:
        to_tag_tracks = mongodb.get_tracks_to_tag()
        tagged_tracks = mongodb.get_tagged_tracks()
        subdatasets = mongodb.get_subdatasets()
        logger.info(f"{len(to_tag_tracks.keys())} tracks to tag read from MongoDb")
        logger.info(f"{len(tagged_tracks)} tagged tracks read from MongoDb")
        logger.info(f"{len(subdatasets)} subdatasets read from MongoDb")

    # Complete already tagged TrackToTags
    for tagged_track in tagged_tracks:
        track = to_tag_tracks.get(tagged_track.track_id, None)
        if track:
            track.label_number = tagged_track.label_number
            track.referee = tagged_track.referee
            track.wrong_track = tagged_track.wrong_track

    bigquery_client = bigquery.Client()
    dataset_id = config["BigQuery"]["dataset"]
    tracks_table_id = config["BigQuery"]["to_tag_table"]
    subdataset_table_id = config["BigQuery"]["sub_dataset_table"]

    # Export tracks to tag
    logger.info(f"Starting tracks export")
    export_data(
        tracks_table_id,
        dataset_id,
        TRACKS_SCHEMA,
        list(to_tag_tracks.values()),
        bigquery_client,
    )
    logger.info(f"Tracks export finished")

    # Export sub datasets
    logger.info(f"Starting sub datasets export")
    export_data(
        subdataset_table_id,
        dataset_id,
        SUBDATASET_SCHEMA,
        subdatasets,
        bigquery_client,
    )
    logger.info(f"Sub datasets export finished")


if __name__ == "__main__":
    export_to_bigquery()
