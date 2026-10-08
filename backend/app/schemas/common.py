from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int = Field(..., description="Total count of matching records")
    skip: int = Field(..., description="Records skipped (offset)")
    limit: int = Field(..., description="Records limit per page")
    has_more: bool = Field(..., description="Whether additional records exist beyond current page")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(..., description="Page items")
    pagination: PaginationMeta
