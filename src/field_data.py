

from dataclasses import dataclass
from typing import Any


@dataclass
class FieldData:
    """FieldData contains data retrieved for a single field"""
    name: str
    type: str
    location: int
    val: Any
