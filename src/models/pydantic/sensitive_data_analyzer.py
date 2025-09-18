from pydantic import BaseModel


class AnalyzerResult(BaseModel):
    entity_type: str
    start: int
    end: int
    score: float
