# schemas/navigation/profileTabSchema/profileScreenSchema.py
from pydantic import BaseModel
from typing import Optional, List

class PublicUserProfile(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    about_me: Optional[str] = None
    profile_image: Optional[str] = None
    is_own_profile: bool = False
    is_following: bool = False
    followers_count: int = 0
    following_count: int = 0

class FollowActionResponse(BaseModel):
    message: str

class UserListItem(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    profile_image: Optional[str] = None
    is_following: bool = False
    show_follow_button: bool = False

class FollowersResponse(BaseModel):
    followers: List[UserListItem]
    count: int

class FollowingResponse(BaseModel):
    following: List[UserListItem]
    count: int