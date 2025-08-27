from app.db.client import db
from bson import ObjectId
from typing import Optional

def get_template(template_id: str) -> Optional[dict]:
    return db.templates.find_one({"_id": ObjectId(template_id)})
