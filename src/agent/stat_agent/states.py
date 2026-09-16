from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages

from __future__ import annotations

from pydantic import BaseModel


class QueryResult(BaseModel):
    tool: str = ""
    columns: list[str] = []
    rows: list[list] = []
    row_count: int = 0
    error: str = ""

class Stat_Input(BaseModel):
    question: str
    
class Stat_Output(BaseModel):
    question: str
    answer: str
    query: QueryResult | None = None
    detail: str = ""


#==============================================
class StatState(TypedDict, total=False):
    question: str
    result: Stat_Output
    messages: Annotated[list, add_messages] 