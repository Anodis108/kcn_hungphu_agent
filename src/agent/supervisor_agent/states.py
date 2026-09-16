from __future__ import annotations

from typing import Annotated, TypedDict, Any

from pydantic import BaseModel

from atin.app.stat_agent.schemas import Agent_Output

class Question_Input(BaseModel):
    question: str
    thread_id: str = ""


class Question_Output(BaseModel):
    question: str
    answer: str
    stat: StatOut | None = None
    thread_id: str = ""
    
    
class SupervisorState(TypedDict, total=False):
    question: str
    final_answer: Question_Output
    output_issues: list[str]
    _trace_span: Any 