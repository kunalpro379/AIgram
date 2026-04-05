from typing import Any, Dict, List, Literal, TypedDict

from pydantic import BaseModel, Field


RoundName = Literal["round_1", "round_2", "final"]


class ChatEvent(TypedDict):
    round: str
    team: str
    speaker: str
    role: str
    message: str


class JudgeThought(TypedDict):
    round: str
    title: str
    thought: str


class DebateState(TypedDict, total=False):
    topic: str
    preferred_language: str
    user_location: str
    user_background: str
    max_cycles: int
    cycle: int
    members_per_team: int

    planner_output: str
    sub_questions: List[str]
    team_a_agents: List[Dict[str, str]]
    team_b_agents: List[Dict[str, str]]
    team_a_context: List[str]
    team_b_context: List[str]

    chat_events: List[ChatEvent]
    judge_thoughts: List[JudgeThought]
    memory: List[str]

    winner: str
    scores: Dict[str, float]
    judge_summary: str
    strategy_update: str
    final_output: Dict[str, Any]


class DebateRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    preferred_language: str = Field(default="English")
    user_location: str = Field(default="")
    user_background: str = Field(default="")
    max_cycles: int = Field(default=1, ge=1, le=4)
    members_per_team: int = Field(default=3, ge=2, le=4)


class ArenaCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    creator_name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)
    image_url: str = Field(default="", max_length=1000)

