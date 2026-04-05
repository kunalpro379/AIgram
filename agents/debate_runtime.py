import json
from dataclasses import dataclass
from typing import Any, Callable, List, Optional


@dataclass
class DebateRuntime:
    llm: Any
    tavily: Any = None
    agno_enabled: bool = False
    event_callback: Optional[Callable[[dict], None]] = None

    def __post_init__(self) -> None:
        try:
            from agno.agent import Agent  # type: ignore[import]
        except Exception:
            self.agno_enabled = False
            return
        self.agno_enabled = True
        self._agno_agent_cls = Agent

    def ask(self, prompt: str) -> str:
        if self.agno_enabled:
            try:
                agent = self._agno_agent_cls(
                    model=self.llm,
                    instructions="Be concise, direct, realistic, slightly informal.",
                )
                result = agent.run(prompt)
                if hasattr(result, "content"):
                    return str(result.content)
                return str(result)
            except Exception:
                pass

        if hasattr(self.llm, "invoke"):
            result = self.llm.invoke(prompt)
            if hasattr(result, "content"):
                return str(result.content)
            return str(result)

        if hasattr(self.llm, "response"):
            return str(self.llm.response(prompt))

        raise RuntimeError("Unsupported LLM object; expected invoke() or response().")

    def web_context(self, query: str, k: int = 3) -> List[str]:
        if not self.tavily:
            return ["Tavily unavailable; configure TAVILY_API_KEY."]
        try:
            result = self.tavily.search(query=query, max_results=k)
            formatted: List[str] = []
            for item in result.get("results", []):
                title = item.get("title", "").strip()
                content = item.get("content", "").strip()
                url = item.get("url", "").strip()
                formatted.append(f"{title}\n{content}\n{url}")
            return formatted or ["No Tavily results found."]
        except Exception as exc:
            return [f"Tavily error: {exc}"]

    def emit(self, event: dict) -> None:
        if self.event_callback:
            self.event_callback(event)


def extract_json(text: str) -> Any:
    cleaned = text.strip()
    try:
        return json.loads(cleaned)
    except Exception:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and start < end:
            return json.loads(cleaned[start : end + 1])
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and start < end:
            return json.loads(cleaned[start : end + 1])
        raise ValueError("No parseable JSON in model output.")

