from typing import List, Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    id: str
    phone: Optional[str] = None
    realName: Optional[str] = None
    nickname: str = "FINDY 회원"


class ConsentInput(BaseModel):
    userId: str
    consentType: str
    isAgreed: bool
    policyVersion: str


class LocationPreferenceInput(BaseModel):
    userId: str
    locationPermissionStatus: str = "not_requested"
    selectedRegion: Optional[str] = None
    locationEnabled: bool = False


class NoticeInput(BaseModel):
    title: str
    body: str
    status: str = "visible"
    pinned: bool = False


class EventInput(BaseModel):
    title: str
    body: str
    status: str = "visible"
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None


class PostInput(BaseModel):
    userId: str
    postType: str = "자유"
    category: str = "전체"
    title: str
    body: str
    tags: List[str] = Field(default_factory=list)


class CommentInput(BaseModel):
    postId: str
    userId: str
    body: str


class ReviewInput(BaseModel):
    userId: str
    placeName: str
    artistName: Optional[str] = None
    serviceCategory: str
    rating: int = Field(ge=1, le=5)
    body: str
    tags: List[str] = Field(default_factory=list)
    verifiedVisit: bool = False


class ReportInput(BaseModel):
    reporterUserId: str
    targetType: str
    targetId: str
    reason: str
    detail: Optional[str] = None


class StatusUpdateInput(BaseModel):
    status: str
    adminMemo: Optional[str] = None
    adminUserId: str = "admin"
    reason: Optional[str] = None


class PointAdjustInput(BaseModel):
    userId: str
    amount: int
    reason: str
    sourceType: str = "admin"
    relatedId: Optional[str] = None
    adminUserId: str = "admin"

