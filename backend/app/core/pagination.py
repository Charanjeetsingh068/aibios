from dataclasses import dataclass
from typing import Optional

from fastapi import Query
from sqlalchemy import asc, desc
from sqlalchemy.sql import Select


@dataclass
class PageParams:
    skip: int
    limit: int
    sort_by: Optional[str]
    sort_dir: str
    search: Optional[str]


def pagination_params(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    search: Optional[str] = Query(None, description="Free-text search term"),
) -> PageParams:
    return PageParams(skip=skip, limit=limit, sort_by=sort_by, sort_dir=sort_dir, search=search)


def apply_sort(query: Select, model, params: PageParams, allowed_columns: set, default_column: str) -> Select:
    """Applies ORDER BY, restricted to `allowed_columns` to prevent sorting by an arbitrary
    (or non-existent) attribute from user input."""
    column_name = params.sort_by if params.sort_by in allowed_columns else default_column
    column = getattr(model, column_name)
    return query.order_by(asc(column) if params.sort_dir == "asc" else desc(column))
