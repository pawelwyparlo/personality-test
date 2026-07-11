# Thin VertexAI adapter, no LangChain/LangGraph

All LLM use (coach chat via SSE streaming, report narrative generation) goes through a small
internal `LLMClient` interface with a single VertexAI implementation configured from `.env`.
We deliberately rejected LangChain/LangGraph for v1: the coach is system-prompt + chat history with
no tools, and the narrative is a single structured-output call — a framework would add a heavy
dependency and leaky abstractions for no used capability. Revisit LangGraph when the coach gains
tools (goal CRUD, scheduled check-ins). The report must always render without an LLM: narrative
generation falls back to the deterministic IPIP text bank (low/average/high per domain/facet) when
no key is configured or the call fails.
