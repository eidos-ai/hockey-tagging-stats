from __future__ import annotations
from pymongo import MongoClient
from pymongo.collection import Collection
from configparser import SectionProxy
from typing import Dict, Any

from tracks_dataclasses import TrackToTag, TaggedTrack, SubDataset


class MongoDBConnect:
    def __init__(self, config: SectionProxy, mongo_uri: str) -> None:
        self._db_name = config["DB_NAME"]
        self._to_tag_collection_name = config["TO_TAG_COLLECTION_NAME"]
        self._tagged_collection_name = config["TAGGED_COLLECTION_NAME"]
        self._sub_dataset_collection_name = config["SUB_DATASET_COLLECTION_NAME"]
        self._mongo_uri = mongo_uri
        self._client = self.connect_to_mongodb(self._mongo_uri)
        self._to_tag_collection = self.load_collection(self._to_tag_collection_name)
        self._tagged_collection = self.load_collection(self._tagged_collection_name)
        self._sub_dataset_collection = self.load_collection(
            self._sub_dataset_collection_name
        )

    def __enter__(self) -> MongoDBConnect:
        return self

    def __exit__(self, error: Exception, value: object, tracebak: object) -> None:
        self.close_connection()

    def connect_to_mongodb(self, mongodb_uri: str) -> MongoClient[Dict[str, Any]]:
        return MongoClient(mongodb_uri)

    def close_connection(self) -> None:
        if self._client:
            self._client.close()

    def load_collection(self, collection_name: str) -> Collection[Dict[str, Any]]:
        db = self._client[self._db_name]
        collection = db[collection_name]
        return collection

    def get_tracks_to_tag(self):
        entries = self._to_tag_collection.find()
        tracks = {}
        for entry in entries:
            track_id = entry.get("track_id", None)
            if track_id:
                tracks[track_id] = TrackToTag(entry)
        return tracks

    def get_tagged_tracks(self):
        entries = self._tagged_collection.find()
        tracks = [TaggedTrack(entry) for entry in entries]
        return tracks

    def get_subdatasets(self):
        entries = self._sub_dataset_collection.find()
        subdatasets = [SubDataset(entry) for entry in entries]
        return subdatasets
