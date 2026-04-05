from typing import Any, Callable, Dict, Optional

from langgraph.graph import END, StateGraph

from LLMs.factory import get_deepseek_chat_model, get_tavily_client

from agents.debate_runtime import DebateRuntime
from states.debate import DebateState
from workflow.nodes_debate import debate_loop_node
from workflow.nodes_judge import final_node, judge_node, strategy_node
from workflow.nodes_planning import context_fetch_node, decomposition_node, planner_node, team_generator_node


def build_graph(runtime: DebateRuntime):
    graph = StateGraph(DebateState)
    graph.add_node("planner", lambda s: planner_node(s, runtime))
    graph.add_node("decompose", lambda s: decomposition_node(s, runtime))
    graph.add_node("team_gen", lambda s: team_generator_node(s, runtime))
    graph.add_node("context", lambda s: context_fetch_node(s, runtime))
    graph.add_node("debate_loop", lambda s: debate_loop_node(s, runtime))
    graph.add_node("judge", lambda s: judge_node(s, runtime))
    graph.add_node("strategy", lambda s: strategy_node(s, runtime))
    graph.add_node("final", lambda s: final_node(s, runtime))

    graph.set_entry_point("planner")
    graph.add_edge("planner", "decompose")
    graph.add_edge("decompose", "team_gen")
    graph.add_edge("team_gen", "context")
    graph.add_edge("context", "debate_loop")
    graph.add_edge("debate_loop", "judge")
    graph.add_edge("judge", "strategy")
    graph.add_edge("strategy", "final")
    graph.add_edge("final", END)
    return graph.compile()


def run(
    topic: str,
    preferred_language: str = "English",
    user_location: str = "",
    user_background: str = "",
    max_cycles: int = 1,
    members_per_team: int = 3,
    event_callback: Optional[Callable[[dict], None]] = None,
) -> Dict[str, Any]:
    llm = get_deepseek_chat_model()
    tavily = get_tavily_client()
    runtime = DebateRuntime(llm=llm, tavily=tavily, event_callback=event_callback)
    graph = build_graph(runtime)
    initial_state: DebateState = {
        "topic": topic,
        "preferred_language": preferred_language,
        "user_location": user_location,
        "user_background": user_background,
        "max_cycles": max_cycles,
        "cycle": 1,
        "members_per_team": members_per_team,
        "memory": [],
    }
    return graph.invoke(initial_state).get("final_output", {})

