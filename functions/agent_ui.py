import gradio as gr


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
            seen = set()

            for i, c in enumerate(citations, start=1):
                paper_id = c.get("paper_id")
                title = c.get("title") or paper_id or f"Source {i}"

                if paper_id in seen:
                    continue
                seen.add(paper_id)

                snippet = c.get("content", "")[:400].strip()

                citation_block += f"\n[{i}] **{title}**\n"
                if snippet:
                    citation_block += f"{snippet}\n"


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
