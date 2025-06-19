from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union

class DataRecord(BaseModel):
    id: int
    timestamp: str = Field(alias="timestamp1")  # 兼容数据库字段名
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
    Floor: Optional[int] = None

    @field_validator('volt1', 'volt2', 'volt3', 'current1', 'current2', 'current3', 
                    'power1', 'power2', 'power3', 'energy1', 'energy2', 'energy3', mode='before')
    @classmethod
    def validate_float_fields(cls, v):
        if v is None or v == '':
            return 0.0
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    @field_validator('id', mode='before')
    @classmethod
    def validate_id(cls, v):
        if v is None or v == '':
            return 0
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

    @field_validator('Floor', mode='before')
    @classmethod
    def validate_floor(cls, v):
        if v is None or v == '':
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    class Config:
        populate_by_name = True
        extra = "ignore"  # 忽略额外的字段 