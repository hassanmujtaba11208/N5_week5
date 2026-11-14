"""Bounded single-agent tool router (ReAct-style decide -> act -> observe)."""
import re
from backend.app.tools.calculator import calculate
from backend.app.tools.datetime_tool import current_datetime

CALC_PATTERN = re.compile(r"^[\d\s.+\-*/()%]+$")
TIME_TERMS = ("time", "date", "today", "tomorrow", "weekday", "current time", "current date")
RAG_TERMS = ("knowledge base", "according to", "rag", "retrieval", "anomaly", "infrastructure",
             "monitoring", "predictive maintenance", "root cause", "sensor", "incident", "semantic search")

class AgentService:
    def __init__(self, rag_service, tool_logger, max_iterations: int = 3):
        self.rag = rag_service
        self.tool_logger = tool_logger
        self.max_iterations = max_iterations

    def _choose_tool(self, query: str):
        q = query.strip().lower()
        if CALC_PATTERN.fullmatch(q) and any(c.isdigit() for c in q) and any(op in q for op in "+-*/%"):
            return "calculator", q
        if any(term in q for term in TIME_TERMS):
            return "datetime", query
        if any(term in q for term in RAG_TERMS):
            return "rag", query
        if any(term in q for term in ("calculate", "compute", "what is", "what's", "solve")) and re.search(r"\d", q):
            expression = re.sub(r"^(please\s+)?(calculate|compute|solve|what is|what's)\s*", "", q).rstrip(" ?")
            if CALC_PATTERN.fullmatch(expression):
                return "calculator", expression
        return None, query

    def ask(self, query: str, top_k: int = 3):
        trace = []
        answer = ""
        # The bounded loop is explicit and cannot exceed max_iterations.
        for iteration in range(1, self.max_iterations + 1):
            tool, tool_input = self._choose_tool(query)
            if tool is None:
                answer = ("I’m not sure which action you need. Please clarify whether you want a calculation, "
                          "a date/time lookup, or a search of the knowledge base.")
                trace.append({"iteration": iteration, "tool": None, "observation": "clarification_required"})
                break
            try:
                if tool == "calculator":
                    result = {"result": calculate(tool_input)}
                    answer = f"Result: {result['result']}"
                elif tool == "datetime":
                    result = current_datetime()
                    answer = (f"Current local date: {result['date']} ({result['weekday']}); "
                              f"time: {result['time']} ({result['timezone']}).")
                else:
                    result = {"results": self.rag.search(tool_input, top_k)}
                    if result["results"]:
                        answer = "Retrieved knowledge-base passages:\n\n" + "\n\n".join(
                            f"{r['rank']}. {r['section']} (similarity {r['similarity']})\n{r['text']}"
                            for r in result["results"]
                        )
                    else:
                        answer = "No sufficiently relevant passage was found in the local knowledge base."
                self.tool_logger.write(event="agent_tool", tool=tool, tool_input=tool_input,
                                       status="success", result=result)
                trace.append({"iteration": iteration, "tool": tool, "observation": "success"})
                return {"answer": answer, "tool_used": tool, "iterations": iteration,
                        "trace": trace, "results": result.get("results", [])}
            except Exception as exc:
                self.tool_logger.write(event="agent_tool", tool=tool, tool_input=tool_input,
                                       status="error", error=str(exc))
                answer = f"The {tool} tool could not complete the request: {exc}"
                trace.append({"iteration": iteration, "tool": tool, "observation": "error"})
                break
        return {"answer": answer, "tool_used": trace[-1]["tool"] if trace else None,
                "iterations": len(trace), "trace": trace, "results": []}
