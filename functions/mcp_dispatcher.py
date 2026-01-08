from typing import Dict, Any, List


class MCPDispatcher:
    def __init__(self, search_engine):
        self.search_engine = search_engine

    def dispatch(
        self,
        action: str,
        query: str,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        if action == "search_metadata":
            return self.search_engine.search_metadata(query, **kwargs)

        if action == "search_chunks":
            return self.search_engine.search_chunks(query, **kwargs)

        raise ValueError(f"Unknown MCP action: {action}")
