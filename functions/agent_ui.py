import gradio as gr
from collections import defaultdict

def launch_agent_ui(agent):
    """
    NotebookLM-style conversational UI.
    Compatible with Gradio >= 6.0 (messages-only Chatbot).
    """

    def agent_chat(query, history):
        """
        history: List[{"role": "user"|"assistant", "content": str}]
        """
        citation_block = ""

        if history is None:
            history = []

        # ---- append user message ----
        history.append(
            {
                "role": "user",
                "content": query,
            }
        )

        # ---- run agent ----
        result = agent.run(query)

        # ---- normalize agent output ----
        if isinstance(result, dict):
            answer = result.get("answer")  # may be None
            citations = result.get("citations", [])
            rationale = result.get("rationale", "")
        else:
            answer = str(result)
            citations = []
            rationale = ""

        # ---- build citation block ----
        if citations:
            citation_block += "\n\n---\n**Sources**\n"

            # paper_id -> list of chunks
            grouped = defaultdict(list)
            for c in citations:
                pid = c.get("paper_id")
                if not pid:
                    continue
                grouped[pid].append(c)

            # enumerate papers
            for paper_idx, (pid, chunks) in enumerate(grouped.items(), start=1):
                title = chunks[0].get("title") or pid

                # Paper header with index
                citation_block += f"\n[{paper_idx}] **{title}**\n"

                # List chunks under this paper
                for c in chunks:
                    content = c.get("content", "").strip()
                    if not content:
                        continue

                    snippet = content[:400]
                    citation_block += f"- {snippet}\n"

        # ---- build final answer safely ----
        if answer is None:
            # Abstain or no-answer case
            full_answer = (
                "I cannot answer this question based on the retrieved evidence.\n\n"
                f"**Reason:** {rationale}"
            )
        else:
            full_answer = answer + citation_block

        # ---- append assistant message ----
        history.append(
            {
                "role": "assistant",
                "content": full_answer,
            }
        )

        return history

    with gr.Blocks() as demo:
        gr.Markdown(
            """
            # Research Agent (NotebookLM-style)

            - One question = one full agent inference
            - Answers are grounded in retrieved literature
            - Sources are explicitly cited
            """
        )

        chatbot = gr.Chatbot(
            label="Conversation",
            height=500,
        )

        query_box = gr.Textbox(
            label="Ask a question",
            placeholder="e.g. What are the best risk reporting practices?",
            lines=2,
        )

        send_btn = gr.Button("Send")

        send_btn.click(
            agent_chat,
            inputs=[query_box, chatbot],
            outputs=[chatbot],
        )

    return demo
