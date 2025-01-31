from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl

class InstagramComment(BaseModel):
    id: str
    postId: str
    text: str
    position: int
    timestamp: datetime
    ownerId: str
    ownerIsVerified: bool
    ownerUsername: str
    ownerProfilePicUrl: HttpUrl

class InstagramPost(BaseModel):
    inputUrl: HttpUrl
    url: HttpUrl
    type: str
    shortCode: str
    caption: Optional[str]
    hashtags: List[str]
    mentions: List[str]
    commentsCount: int
    firstComment: Optional[str]
    latestComments: List[InstagramComment]
    dimensionsHeight: int
    dimensionsWidth: int
    displayUrl: HttpUrl
    images: List[str]
    alt: Optional[str]
    likesCount: int
    timestamp: datetime
    childPosts: List[dict]
    ownerFullName: str
    ownerUsername: str
    ownerId: str
    isSponsored: bool

class ScraperConfig(BaseModel):
    addParentData: bool
    directUrls: List[HttpUrl]
    enhanceUserSearchWithFacebookPage: bool
    isUserReelFeedURL: bool
    isUserTaggedFeedURL: bool
    resultsLimit: int
    resultsType: str
    searchLimit: int
    searchType: str 