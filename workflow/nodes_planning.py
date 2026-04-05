from typing import Any, Dict, List

from agents.debate_runtime import DebateRuntime, extract_json
from prompts.debate import decomposition_prompt, planner_prompt, team_gen_prompt
from states.debate import DebateState


def planner_node(state: DebateState, runtime: DebateRuntime) -> Dict[str, Any]:
    runtime.emit(
        {
            "type": "agent_activity",
            "agent": "Meta-Agent Planner",
            "stage": "planning",
            "thought": "Understanding user context and framing debate strategy.",
        }
    )
    prompt = planner_prompt(
        state["topic"],
        state.get("preferred_language", "English"),
        state.get("user_location", ""),
        state.get("user_background", ""),
    )
    planner_output = runtime.ask(prompt).strip()
    runtime.emit({"type": "planner", "planner_output": planner_output})
    return {"planner_output": planner_output}


def decomposition_node(state: DebateState, runtime: DebateRuntime) -> Dict[str, Any]:
    runtime.emit(
        {
            "type": "agent_activity",
            "agent": "Task Decomposer",
            "stage": "decomposition",
            "thought": "Breaking topic into key sub-questions for both teams.",
        }
    )
    prompt = decomposition_prompt(
        state["topic"],
        state.get("planner_output", ""),
        state.get("preferred_language", "English"),
    )
    fallback = [
        "What is the exact scope?",
        "What are strongest benefits?",
        "What are strongest risks?",
        "Where does evidence disagree?",
        "What practical recommendation follows?",
    ]
    try:
        items = extract_json(runtime.ask(prompt))
        if not isinstance(items, list):
            raise ValueError("Expected list.")
        sub_questions = [str(x) for x in items][:5]
    except Exception:
        sub_questions = fallback
    memory_line = f"Sub-questions: {', '.join(sub_questions)}"
    memory = state.get("memory", [])
    memory.append(memory_line)
    runtime.emit({"type": "sub_questions", "sub_questions": sub_questions})
    return {"sub_questions": sub_questions, "memory": memory}


def team_generator_node(state: DebateState, runtime: DebateRuntime) -> Dict[str, Any]:
    members = int(state.get("members_per_team", 3))
    runtime.emit(
        {
            "type": "agent_activity",
            "agent": "Team Generator",
            "stage": "team_generation",
            "thought": "Creating human-like debaters with complementary roles.",
        }
    )
    prompt = team_gen_prompt(
        state["topic"],
        members,
        state.get("preferred_language", "English"),
        state.get("user_location", ""),
    )
    fallback_a = [
        {"name": "Aarav Mehta", "role": "Lead Advocate"},
        {"name": "Riya Sen", "role": "Evidence Specialist"},
        {"name": "Kabir Jain", "role": "Rebuttal Lead"},
    ][:members]
    fallback_b = [
        {"name": "Zoya Khan", "role": "Critical Examiner"},
        {"name": "Nikhil Rao", "role": "Risk Specialist"},
        {"name": "Mira Das", "role": "Counter-Rebuttal"},
    ][:members]

    def _normalize_team(raw_team: Any, fallback: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not isinstance(raw_team, list):
            return fallback
        clean: List[Dict[str, str]] = []
        for i, member in enumerate(raw_team[:members]):
            if not isinstance(member, dict):
                continue
            name = str(member.get("name", "")).strip()
            role = str(member.get("role", "")).strip()
            # Guardrail: keep names human-like even if model outputs placeholders.
            if len(name.split()) < 2 or any(tok in name.lower() for tok in ("agent", "bot", "assistant")):
                if i < len(fallback):
                    name = fallback[i]["name"]
            if not role:
                role = fallback[i]["role"] if i < len(fallback) else "Debater"
            clean.append({"name": name, "role": role})
        if len(clean) < members:
            clean.extend(fallback[len(clean) : members])
        return clean[:members]

    try:
        data = extract_json(runtime.ask(prompt))
        team_a = _normalize_team(data.get("team_a", []), fallback_a)
        team_b = _normalize_team(data.get("team_b", []), fallback_b)
        if not team_a or not team_b:
            raise ValueError("Team list empty.")
    except Exception:
        team_a, team_b = fallback_a, fallback_b

    runtime.emit({"type": "teams", "team_a": team_a, "team_b": team_b})
    runtime.emit({"type": "team_ready", "team": "team_a", "message": "Team A is ready."})
    runtime.emit({"type": "team_ready", "team": "team_b", "message": "Team B is ready."})

    return {
        "team_a_agents": team_a,
        "team_b_agents": team_b,
        "chat_events": [],
        "judge_thoughts": [],
    }


def context_fetch_node(state: DebateState, runtime: DebateRuntime) -> Dict[str, Any]:
    topic = state["topic"]
    team_a_queries = [
        f"{topic} latest supporting data 2025 2026",
        f"{topic} recent successful case studies",
    ]
    team_b_queries = [
        f"{topic} latest criticism 2025 2026",
        f"{topic} recent failures and risks",
    ]
    team_a_context: List[str] = []
    team_b_context: List[str] = []
    runtime.emit(
        {
            "type": "agent_activity",
            "agent": "Research Agent (Team A)",
            "stage": "research",
            "thought": "Fetching supportive evidence from latest web sources.",
        }
    )
    for q in team_a_queries:
        team_a_context.extend(runtime.web_context(q, k=2))
    runtime.emit(
        {
            "type": "agent_activity",
            "agent": "Research Agent (Team B)",
            "stage": "research",
            "thought": "Fetching critical and risk-focused web evidence.",
        }
    )
    for q in team_b_queries:
        team_b_context.extend(runtime.web_context(q, k=2))
    runtime.emit({"type": "context_ready"})
    return {"team_a_context": team_a_context[:5], "team_b_context": team_b_context[:5]}

