# schemas/navigation/searchSchema.py
from pydantic import BaseModel
from typing import Optional

class SearchUserResult(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    profile_image: Optional[str] = None
