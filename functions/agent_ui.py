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
            answer = result.get("answer", "")
            citations = result.get("citations", [])
        else:
            answer = str(result)
            citations = []

        # ---- build citation block ----
        citation_block = ""
        if citations:
            citation_block += "\n\n---\n**Sources**\n"
            for i, c in enumerate(citations, start=1):
                source_id = c.get("paper_id", f"source-{i}")
                snippet = c.get("content", "")[:500]
                citation_block += f"\n[{i}] `{source_id}`\n{snippet}\n"

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
