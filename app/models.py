from pydantic import BaseModel, Field
from typing import Optional

class DataRecord(BaseModel):
    id: int
    timestamp: str                # ← 字段改名
    volt1: float
    volt2: float
    volt3: float
    current1: float
    current2: float
    current3: float
    power1: float
    power2: float
    power3: float
    energy1: float
    energy2: float
    energy3: float
    Building: str = Field(..., alias="Building")
    Floor: Optional[int]            # 有些旧数据 Floor 可能 NULL 