from typing import Any, Dict

from agents.debate_runtime import DebateRuntime, extract_json
from prompts.debate import final_judge_prompt, strategy_prompt
from states.debate import DebateState


def judge_node(state: DebateState, runtime: DebateRuntime) -> Dict[str, Any]:
    runtime.emit(
        {
            "type": "agent_activity",
            "agent": "Judge Agent",
            "stage": "final_scoring",
            "thought": "Comparing both teams on evidence, logic, and rebuttal quality.",
        }
    )
    # Judge evaluates combined outputs across all configured rounds.
    a_msgs = [m["message"] for m in state.get("chat_events", []) if m["team"] == "team_a"]
    b_msgs = [m["message"] for m in state.get("chat_events", []) if m["team"] == "team_b"]
    prompt = final_judge_prompt(
        state["topic"],
        a_msgs,
        b_msgs,
        state.get("preferred_language", "English"),
    )
    try:
        data = extract_json(runtime.ask(prompt))
        team_a_score = float(data["team_a_score"])
        team_b_score = float(data["team_b_score"])
        judge_summary = str(data["judge_summary"])
    except Exception:
        team_a_score, team_b_score = 50.0, 50.0
        judge_summary = "Could not parse scoring cleanly; applied neutral fallback."

    winner = "team_a" if team_a_score >= team_b_score else "team_b"
    runtime.emit(
        {
            "type": "score",
            "scores": {"team_a": team_a_score, "team_b": team_b_score},
            "winner": winner,
            "judge_summary": judge_summary,
        }
    )
    return {
        "winner": winner,
        "scores": {"team_a": team_a_score, "team_b": team_b_score},
        "judge_summary": judge_summary,
    }


def strategy_node(state: DebateState, runtime: DebateRuntime) -> Dict[str, Any]:
    runtime.emit(
        {
            "type": "agent_activity",
            "agent": "Strategy Coach",
            "stage": "post_analysis",
            "thought": "Drafting improvement advice based on judge decision.",
        }
    )
    prompt = strategy_prompt(
        topic=state["topic"],
        scores=state.get("scores", {}),
        judge_summary=state.get("judge_summary", ""),
        preferred_language=state.get("preferred_language", "English"),
    )
    strategy_update = runtime.ask(prompt).strip()
    runtime.emit({"type": "strategy_update", "strategy_update": strategy_update})
    return {"strategy_update": strategy_update}

def final_node(state: DebateState, runtime: DebateRuntime) -> Dict[str, Any]:
    final_output = {
        "topic": state["topic"],
        "teams": {
            "team_a": state.get("team_a_agents", []),
            "team_b": state.get("team_b_agents", []),
        },
        "chat_events": state.get("chat_events", []),
        "judge_thoughts": state.get("judge_thoughts", []),
        "scores": state.get("scores", {}),
        "winner": state.get("winner", "team_a"),
        "judge_summary": state.get("judge_summary", ""),
        "strategy_update": state.get("strategy_update", ""),
    }
    runtime.emit({"type": "final_output", "result": final_output})
    return {"final_output": final_output}

