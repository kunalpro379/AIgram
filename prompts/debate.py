def planner_prompt(topic: str, preferred_language: str, user_location: str, user_background: str) -> str:
    return f"""
You are a Meta-Agent Planner.
Topic: {topic}
Audience language preference: {preferred_language}
Audience location: {user_location or "Not provided"}
Audience context/background: {user_background or "Not provided"}

Create a tight strategy for two debate teams.
Output <= 120 words.
"""


def decomposition_prompt(topic: str, planner_output: str, preferred_language: str) -> str:
    return f"""
Topic: {topic}
Planner: {planner_output}
Preferred language: {preferred_language}

Break into 5 sub-questions as JSON list of strings only.
"""


def team_gen_prompt(topic: str, members: int, preferred_language: str, user_location: str) -> str:
    return f"""
Topic: {topic}
Preferred language: {preferred_language}
Audience location: {user_location or "Not provided"}
Generate 2 debate teams with human first+last names and roles.
Team A is PRO topic. Team B is AGAINST topic.
Need exactly {members} members per team.

Return strict JSON:
{{
  "team_a": [{{"name":"...", "role":"..."}}],
  "team_b": [{{"name":"...", "role":"..."}}]
}}
"""


def speaker_prompt(
    topic: str,
    team_label: str,
    speaker_name: str,
    speaker_role: str,
    round_name: str,
    context_block: str,
    opponent_json: str,
    own_team_history_json: str,
    opponent_team_history_json: str,
    memory_block: str,
    preferred_language: str,
    user_location: str,
    user_background: str,
) -> str:
    return f"""
You are {speaker_name} from {team_label}. Your role: {speaker_role}.
Debate topic: {topic}
Round: {round_name}
Audience language: {preferred_language}
Audience location: {user_location or "Not provided"}
Audience background: {user_background or "Not provided"}

Your style:
- Talk like a human debater in chat.
- Small natural mistakes/spelling allowed.
- You may lightly roast opponents, but avoid hate/abuse.
- Use language that matches audience preference (Hindi/English/Marathi/other).
- Be culturally respectful and relevant to audience context.
- 45-90 words, no markdown list, no JSON.
- Speak to other debaters directly, not to a crowd or audience.
- Do NOT start with audience-address phrases like "friends", "mitrano", "ladies and gentlemen", or "everyone".
- Prefer direct references like opponent names/roles (for example: "Meghna, your point misses...").
- Ground claims in the provided web context when relevant, and favor recent facts or developments.

Team context:
{context_block}

Opponent latest:
{opponent_json}

Own team chat history:
{own_team_history_json}

Opponent team chat history:
{opponent_team_history_json}

Memory:
{memory_block}

Interaction rules:
- You should react to prior chat messages from BOTH teams.
- Support and build on your own teammates when their point is strong.
- Oppose weak or flawed opponent points clearly.
- If opponent makes a valid point, acknowledge briefly, then respond with nuance.
- Do not repeat your own earlier point in the same wording or close paraphrase.
- Add at least one new angle each turn (new evidence, example, mechanism, or consequence).
"""


def live_judge_prompt(topic: str, round_name: str, recent_messages_json: str, preferred_language: str) -> str:
    return f"""
You are live judge observing debate.
Topic: {topic}
Current round: {round_name}
Audience language: {preferred_language}
Recent messages:
{recent_messages_json}

Give one short internal thought (<= 40 words), candid and direct.
"""


def final_judge_prompt(topic: str, a_msgs: list[str], b_msgs: list[str], preferred_language: str) -> str:
    return f"""
You are final judge.
Topic: {topic}
Audience language: {preferred_language}
Team A sample: {a_msgs}
Team B sample: {b_msgs}

Score each team 0-100 based on evidence, logic, and rebuttal.
Return strict JSON:
{{
  "team_a_score": 0,
  "team_b_score": 0,
  "judge_summary": "..."
}}
"""


def strategy_prompt(topic: str, scores: dict, judge_summary: str, preferred_language: str) -> str:
    return f"""
Topic: {topic}
Scores: {scores}
Judge summary: {judge_summary}
Audience language: {preferred_language}

Provide one strategy update for future debate in <= 50 words.
"""

