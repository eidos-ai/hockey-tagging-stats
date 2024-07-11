from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any


@dataclass
class TrackToTag:
    track_id: str
    game_id: str
    dataset_name: str
    detected_label: str
    status: str
    assigned_user: str
    assign_date: datetime
    detection_model: str
    label_number: str | None
    referee: bool | None
    wrong_track: bool | None

    def __init__(self, params: dict[str, Any]) -> None:
        self.track_id = params["track_id"]
        self.game_id = params["game_id"]
        self.dataset_name = params["dataset_name"]
        self.detected_label = params["detected_label"]
        self.status = params["status"]
        self.assigned_user = params["assigned_user"]
        self.assign_date = params["assign_date"]
        self.detection_model = params["detection_model"]
        self.label_number = None
        self.referee = None
        self.wrong_track = None

    def dict(self):
        return asdict(self)


@dataclass
class TaggedTrack:
    track_id: str
    label_number: str
    referee: bool
    wrong_track: bool

    def __init__(self, params: dict[str, Any]) -> None:
        self.track_id = params["track_id"]
        self.label_number = params["label_number"]
        self.referee = params["referee"]
        self.wrong_track = params["wrong_track"]

    def dict(self):
        return asdict(self)


@dataclass
class SubDataset:
    dataset_name: str
    sub_dataset_name: str
    creation_time: datetime
    number_of_tracks: int

    def __init__(self, params: dict[str, Any]) -> None:
        self.dataset_name = params["dataset_name"]
        self.sub_dataset_name = params["sub_dataset_name"]
        self.creation_time = params["creation_time"]
        self.number_of_tracks = len(params["labels"])

    def dict(self):
        return asdict(self)
