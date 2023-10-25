import typing as t
from pathlib import Path
from abc import ABC, abstractmethod
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class TimeEntry:
    last_changed: datetime
    device_type: str
    device_name: str
    state: str

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, __class__):
            return self.last_changed == __value.last_changed
        raise NotImplemented()
    
    def __gt__(self, __value: object) -> bool:
        if isinstance(__value, __class__):
            return self.last_changed > __value.last_changed
        raise NotImplemented()
    
    def __lt__(self, __value: object) -> bool:
        if isinstance(__value, __class__):
            return self.last_changed < __value.last_changed
        raise NotImplemented()
    
class SQLiteDB:
    def __init__(self, location: int):
        pass