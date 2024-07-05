from __future__ import annotations
from pymongo import MongoClient
from pymongo.collection import Collection
from configparser import SectionProxy
from typing import Dict, Any


DB_FIELD_BILLED = "cost_per_hour"


class MongoDBConnect:
    def __init__(self, config: SectionProxy, mongo_uri: str) -> None:
        self._db_name = config["DB_NAME"]
        self._timelog_collection_name = config["TIMELOG_COLLECTION_NAME"]
        self._project_collection_name = config["PROJECT_COLLECTION_NAME"]
        self._mongo_uri = mongo_uri
        self._client = self.connect_to_mongodb(self._mongo_uri)
        self._timelog_collection = self.load_collection(self._timelog_collection_name)
        self._project_collection = self.load_collection(self._project_collection_name)

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