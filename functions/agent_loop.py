import json
from functions.agent_state import AgentState
from functions.reasoning_schema import ReasoningOutput
from functions.intent_router import IntentRouter
from collections import OrderedDict

class AgenticInference:
    def __init__(
        self,
        llm,
        search_engine,
        context_builder,
        prompt_synthesizer,
        mcp_dispatcher,
    ):
        self.llm = llm
        self.search_engine = search_engine
        self.context_builder = context_builder
        self.prompt_synthesizer = prompt_synthesizer
        self.mcp = mcp_dispatcher
        self.router = IntentRouter(llm)

    def run(self, query: str) -> str:

        intent = self.router.route(query)
        print(f"=== DETECTED INTENT: {intent} ===")

        if intent in ["GREETING", "SELF_INFO", "GENERAL_KNOWLEDGE"]:
            direct_prompt = f"""
            You are a helpful Research Assistant specialized in Physiological Signal Analysis (ECG/PCG).
            
            User Intent: {intent}
            User Query: {query}
            
            Please respond politely and concisely. Do NOT hallucinate retrieved papers.
            """
            response_text = self.llm(direct_prompt)
            
            return {
                "answer": response_text,
                "citations": []
            }
        
        state = AgentState(
            original_query=query,
            canonical_query=query.lower().strip(),
            current_goal="Answer the user's question using retrieved evidence.",
        )

        while not state.should_terminate():
            state.iteration += 1

            # --- If no evidence yet, start with metadata search ---
            if not state.retrieval_results:
                results = self.mcp.dispatch(
                    action="search_metadata",
                    query=state.canonical_query,
                    k=5,
                )
                state.retrieval_results = results
                state.last_retrieval_type = "metadata"

            if state.last_retrieval_type == "metadata":
            #     state.candidate_papers = {
            #         r["paper_id"] for r in state.retrieval_results if "paper_id" in r
            #     }
                state.paper_metadata = {
                    r["paper_id"]: {
                        "title": r.get("title"),
                        "abstract": r.get("abstract"),
                    }
                    for r in state.retrieval_results
                    if r.get("paper_id")
                }

                state.candidate_papers = set(state.paper_metadata.keys())

                state.retrieval_results = self.mcp.dispatch(
                    action="search_chunks",
                    query=state.canonical_query,
                    k=10,
                    paper_ids=list(state.candidate_papers),
                )
                state.last_retrieval_type = "chunks"
                continue

            # --- Build context ---
            # if state.last_retrieval_type == "chunks":
            #     state.context_bundle = self.context_builder.build(
            #         state.retrieval_results
            #     )
            print("PAPER METADATA:", state.paper_metadata)

            if state.last_retrieval_type == "chunks":
                for chunk in state.retrieval_results:
                    pid = chunk.get("paper_id")
                    if pid in state.paper_metadata:
                        chunk["title"] = state.paper_metadata[pid].get("title")

                state.context_bundle = self.context_builder.build(
                    state.retrieval_results
                )
            else:
                state.context_bundle = None


            print("=== CONTEXT BUNDLE ===")
            print(state.context_bundle)
            print("======================")

            # --- Synthesize prompt ---
            prompt = self.prompt_synthesizer.synthesize(
                question=state.original_query,
                context_bundle=state.context_bundle,
                current_goal=state.current_goal,
            )

            # --- LLM reasoning ---
            raw_output = self.llm(prompt)
            print("=== RAW LLM OUTPUT ===")
            print(raw_output)
            print("======================")

            try:
                reasoning: ReasoningOutput = json.loads(raw_output)
            except Exception:
                state.terminated = True
                state.termination_reason = "Invalid LLM output"
                break

            state.last_llm_output = reasoning

            # --- Decision ---
            # decision = reasoning["decision"]
            decision = reasoning["decision"]
            rationale = reasoning.get("reasoning", {}).get("rationale")

            print("=== AGENT REASONING ===")
            print("Decision:", decision)
            print("Rationale:", rationale)
            print("======================")

            if decision == "answer" and state.last_retrieval_type != "chunks":
                raise RuntimeError("Answer generated without chunk-level evidence")

            if decision == "answer":
                state.terminated = True

                paper_map = OrderedDict()

                for item in state.context_bundle.get("items", []):
                    pid = item["paper_id"]
                    if pid not in paper_map:
                        paper_map[pid] = {
                            "paper_id": pid,
                            "title": item.get("title"),
                            "chunks": []
                        }
                    paper_map[pid]["chunks"].append({
                        "content": item.get("content"),
                        "source_id": item.get("source_id")
                    })

                citations = []
                for idx, paper in enumerate(paper_map.values(), start=1):
                    paper["order"] = idx
                    citations.append(paper)

                return {
                    "answer": reasoning.get("answer", ""),
                    "citations": citations
                }


            # --- METADATA SEARCH ---
            elif decision == "search_metadata":
                results = self.mcp.dispatch(
                    action="search_metadata",
                    query=state.canonical_query,
                    k=5,
                )

                state.retrieval_results = results

                print("=== RETRIEVAL RESULTS ===")
                print(state.retrieval_results[:2])
                print("=========================")

                state.candidate_papers = {
                    r["paper_id"] for r in results if "paper_id" in r
                }

                continue

            # --- CHUNK SEARCH ---
            elif decision == "search_chunks":
                paper_ids = (
                    list(state.candidate_papers)
                    if state.candidate_papers
                    else None
                )

                state.retrieval_results = self.mcp.dispatch(
                    action="search_chunks",
                    query=state.canonical_query,
                    k=10,
                    paper_ids=paper_ids,
                )

                continue

            # --- ABSTAIN ---
            # elif decision == "abstain":
            #     state.terminated = True
            #     state.termination_reason = "Abstained"
            #     return "I cannot answer this question with the available information."
            # elif decision == "abstain":
            #     rationale = reasoning.get("reasoning", {}).get("rationale")
            #     if not rationale:
            #         raise RuntimeError("ABSTAIN without decision_rationale — schema mismatch")
            elif decision == "abstain":
                state.terminated = True
                state.termination_reason = "Abstained due to insufficient evidence"
                return {
                    "answer": None,
                    "rationale": rationale,
                    "citations": []
                }

        return "Inference terminated without a confident answer."
