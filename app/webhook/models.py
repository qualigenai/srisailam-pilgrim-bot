from pydantic import BaseModel
from typing import Optional, List

class AWPArtifact(BaseModel):
    artifact_type: str  # Renamed from 'type' to avoid shadowing built-in names
    data: str
    confidence: float
    source_citations: Optional[List[str]] = None