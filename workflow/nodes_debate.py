import asyncio
import json
import random
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List

from agents.debate_runtime import DebateRuntime
from prompts.debate import live_judge_prompt, speaker_prompt
from states.debate import ChatEvent, DebateState, JudgeThought, RoundName


def _speaker_prompt(
    state: DebateState,
    team_key: str,
    speaker: Dict[str, str],
    round_name: str,
    opponent_messages: List[ChatEvent],
    own_team_messages: List[ChatEvent],
) -> str:
    team_label = "Team A (PRO)" if team_key == "team_a" else "Team B (AGAINST)"
    context = state.get("team_a_context", []) if team_key == "team_a" else state.get("team_b_context", [])
    # Keep cumulative memory across all rounds in this run.
    recent_memory = "\n".join(state.get("memory", []))
    opponent_json = json.dumps(opponent_messages[-3:], ensure_ascii=True)
    own_team_history_json = json.dumps(own_team_messages[-10:], ensure_ascii=True)
    opponent_team_history_json = json.dumps(opponent_messages[-10:], ensure_ascii=True)
    context_block = "\n".join(context[:3])
    return speaker_prompt(
        topic=state["topic"],
        team_label=team_label,
        speaker_name=speaker["name"],
        speaker_role=speaker["role"],
        round_name=round_name,
        context_block=context_block,
        opponent_json=opponent_json,
        own_team_history_json=own_team_history_json,
        opponent_team_history_json=opponent_team_history_json,
        memory_block=recent_memory,
        preferred_language=state.get("preferred_language", "English"),
        user_location=state.get("user_location", ""),
        user_background=state.get("user_background", ""),
    )


async def _parallel_speakers(
    runtime: DebateRuntime,
    prompts: List[Dict[str, Any]],
) -> List[ChatEvent]:
    async def run_one(item: Dict[str, Any]) -> ChatEvent:
        text = await asyncio.to_thread(runtime.ask, item["prompt"])
        return {
            "round": item["round"],
            "team": item["team"],
            "speaker": item["speaker"]["name"],
            "role": item["speaker"]["role"],
            "message": text.strip(),
        }

    return await asyncio.gather(*(run_one(p) for p in prompts))


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"[^\w\s]", "", lowered)
    return lowered.strip()


def _is_repetitive(candidate: str, recent_messages: List[str], threshold: float = 0.84) -> bool:
    norm_candidate = _normalize_text(candidate)
    if not norm_candidate:
        return True
    for prev in recent_messages:
        norm_prev = _normalize_text(prev)
        if not norm_prev:
            continue
        if norm_candidate == norm_prev:
            return True
        if SequenceMatcher(None, norm_candidate, norm_prev).ratio() >= threshold:
            return True
    return False


def debate_loop_node(state: DebateState, runtime: DebateRuntime) -> Dict[str, Any]:
    chat_events = state.get("chat_events", [])
    judge_thoughts: List[JudgeThought] = state.get("judge_thoughts", [])
    memory = state.get("memory", [])
    rounds_count = int(state.get("max_cycles", 1))
    rounds: List[str] = [f"round_{i}" for i in range(1, rounds_count + 1)]

    for round_name in rounds:
        runtime.emit(
            {
                "type": "agent_activity",
                "agent": "Debate Controller",
                "stage": "round_start",
                "thought": f"Starting {round_name}. Coordinating Team A and Team B speakers.",
            }
        )
        # Dynamic open-floor debate:
        # - mixed team order
        # - same speaker can appear multiple times
        # - no strict turn restriction
        team_a_agents = state["team_a_agents"]
        team_b_agents = state["team_b_agents"]
        turns_this_round = max(8, (len(team_a_agents) + len(team_b_agents)) * 2)
        generated: List[ChatEvent] = []
        speaker_cooldown = 2

        for _ in range(turns_this_round):
            # Soft anti-monopoly guard: avoid same team dominating long streaks.
            last_two = generated[-2:]
            if len(last_two) == 2 and last_two[0]["team"] == last_two[1]["team"]:
                team_key = "team_b" if last_two[-1]["team"] == "team_a" else "team_a"
            else:
                team_key = random.choice(["team_a", "team_b"])

            speaker_pool = team_a_agents if team_key == "team_a" else team_b_agents
            recent_speakers = [x["speaker"] for x in generated[-speaker_cooldown:]]
            eligible = [s for s in speaker_pool if s["name"] not in recent_speakers]
            speaker = random.choice(eligible or speaker_pool)

            team_a_history = [x for x in chat_events if x["team"] == "team_a"]
            team_b_history = [x for x in chat_events if x["team"] == "team_b"]
            opponent_messages = team_b_history if team_key == "team_a" else team_a_history
            own_team_messages = team_a_history if team_key == "team_a" else team_b_history

            runtime.emit(
                {
                    "type": "agent_activity",
                    "agent": speaker["name"],
                    "stage": "message_prep",
                    "thought": f"Preparing {round_name} argument for {'Team A' if team_key == 'team_a' else 'Team B'}.",
                }
            )

            prompt = _speaker_prompt(
                state,
                team_key,
                speaker,
                round_name,
                opponent_messages,
                own_team_messages,
            )
            recent_same_team_msgs = [x["message"] for x in chat_events if x["team"] == team_key][-6:]
            recent_all_msgs = [x["message"] for x in chat_events][-4:]
            text = runtime.ask(prompt).strip()
            if _is_repetitive(text, recent_same_team_msgs + recent_all_msgs):
                rewrite_prompt = (
                    f"{prompt}\n\n"
                    "Your previous draft was too repetitive. Rewrite with a NEW angle.\n"
                    "Hard constraints:\n"
                    "- Do not reuse prior phrasing.\n"
                    "- Introduce one fresh claim, example, or evidence point.\n"
                    "- Directly rebut one specific opponent point from recent messages.\n"
                )
                rewritten = runtime.ask(rewrite_prompt).strip()
                if not _is_repetitive(rewritten, recent_same_team_msgs + recent_all_msgs):
                    text = rewritten
            event: ChatEvent = {
                "round": round_name,
                "team": team_key,
                "speaker": speaker["name"],
                "role": speaker["role"],
                "message": text,
            }
            generated.append(event)
            chat_events.append(event)
            runtime.emit({"type": "chat_event", "data": event})

        judge_prompt = live_judge_prompt(
            topic=state["topic"],
            round_name=round_name,
            recent_messages_json=json.dumps(generated[-4:], ensure_ascii=True),
            preferred_language=state.get("preferred_language", "English"),
        )
        runtime.emit(
            {
                "type": "agent_activity",
                "agent": "Judge Agent",
                "stage": "live_review",
                "thought": f"Reviewing recent exchanges for {round_name}.",
            }
        )
        judge_note = runtime.ask(judge_prompt).strip()
        judge_thoughts.append(
            {
                "round": round_name,
                "title": f"Judge thought after {round_name}",
                "thought": judge_note,
            }
        )
        runtime.emit({"type": "judge_thought", "data": judge_thoughts[-1]})
        memory.append(f"{round_name}: {judge_note}")

    return {"chat_events": chat_events, "judge_thoughts": judge_thoughts, "memory": memory}

