from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RawPaths(BaseModel):
    pdf: Optional[str] = None
    latex: Optional[str] = None
    docx: Optional[str] = None
    code: Optional[List[str]] = None
    data: Optional[List[str]] = None
    other: Optional[List[str]] = None

class DiscussionPost(BaseModel):
    platform: str
    thread_url: Optional[str] = None
    post_id: Optional[str] = None
    author: Optional[str] = None
    created: Optional[str] = None  # ISO
    body: Optional[str] = None
    reply_to: Optional[str] = None

class Record(BaseModel):
    source: str
    id: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    authors: Optional[List[str]] = None
    date: Optional[str] = None       # ISO date
    subject: Optional[str] = None
    journal: Optional[str] = None
    comments: Optional[str] = None
    doi: Optional[str] = None
    revision: Optional[int] = None
    length_chars: Optional[int] = None
    sections: Optional[int] = None
    source_url: Optional[str] = None
    file_type: Optional[str] = None
    raw_paths: RawPaths = Field(default_factory=RawPaths)
    clean_text_path: Optional[str] = None
    discussions: Optional[List[DiscussionPost]] = None
    extra: Dict[str, Any] = Field(default_factory=dict)
