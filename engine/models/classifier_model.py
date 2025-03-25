from typing import List
from pydantic import BaseModel


class ClassifierBase(BaseModel):
    category: str
    probability: float

class ClassifierOutput(BaseModel):
    result: List[ClassifierBase]
