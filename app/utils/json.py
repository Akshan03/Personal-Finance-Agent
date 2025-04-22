"""
Utility functions for JSON serialization of MongoDB objects
"""
import json
from bson import ObjectId
from typing import Any, Dict, List

class MongoJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles MongoDB ObjectId types
    """
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

def parse_json(data: Any) -> Any:
    """
    Convert MongoDB objects to serializable Python types
    """
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, list):
        return [parse_json(item) for item in data]
    elif isinstance(data, dict):
        return {key: parse_json(value) for key, value in data.items()}
    return data
