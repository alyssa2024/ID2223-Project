import gradio as gr
from collections import defaultdict

def launch_agent_ui(agent):
    """
    NotebookLM-style conversational UI for Gradio 6.3+.
    Features:
    - Messages API (type="messages")
    - Auto-clear input on submit
    - Enter key submission
    - Clean citations (no scores)
    """

    def agent_chat(query, history):
        """
        Input: 
            query: str
            history: List[dict] (Gradio 6.0+ format: [{"role": "user", "content": "..."}])
        Output: 
            updated_query (str): Empty string to clear input
            updated_history (List[dict]): New conversation history
        """
        # 1. Handle empty input
        if not query.strip():
            return "", history

        if history is None:
            history = []

        # 2. Append User Message immediately
        history.append({"role": "user", "content": query})

        # 3. Run Agent (Inference)
        try:
            result = agent.run(query)
        except Exception as e:
            # Fallback for errors
            error_msg = f"⚠️ System Error: {str(e)}"
            history.append({"role": "assistant", "content": error_msg})
            return "", history

        # 4. Parse Agent Result
        if isinstance(result, dict):
            answer = result.get("answer")
            citations = result.get("citations", [])
            rationale = result.get("rationale", "")
        else:
            answer = str(result)
            citations = []
            rationale = ""

        # 5. Build Citation Block (Clean Version - No Scores)
        citation_block = ""
        if citations:
            citation_block += "\n\n---\n**Sources**\n"

            for paper in citations:
                order = paper["order"]
                title = paper["title"]

                citation_block += f"\n[{order}] **{title}**\n"
                citation_block += "<details><summary>View evidence</summary>\n\n"

                for ch in paper.get("chunks", []):
                    snippet = ch["content"][:300].replace("\n", " ") + "..."
                    citation_block += f"- {snippet}\n"

                citation_block += "\n</details>\n" 

        # 6. Construct Final Response
        if not answer:
            # Abstain case
            full_response = (
                "I cannot answer this question based on the retrieved evidence.\n\n"
                f"**Reasoning:** {rationale}"
            )
        else:
            full_response = answer + citation_block

        history.append({"role": "assistant", "content": full_response})
        
        # Return empty string to clear the Textbox, and updated history
        return "", history

    # ---- UI Layout ----
    with gr.Blocks(title="Research Agent", theme=gr.themes.Soft()) as demo:
        gr.Markdown("## 🏥 Medical Research Agent")
        
        # Gradio 6.x specific: type="messages" handles list[dict] history natively
        chatbot = gr.Chatbot(
            label="Conversation", 
            height=600,
            avatar_images=(None, "https://api.dicebear.com/9.x/bottts/svg?seed=ResearchAgent")
        )

        with gr.Row():
            query_box = gr.Textbox(
                label="Your Question",
                placeholder="Ask about medical research papers...",
                scale=4,
                lines=1, # Single line encourages "Enter" to submit
                autofocus=True
            )
            send_btn = gr.Button("Send", variant="primary", scale=1)

        # ---- Event Bindings ----
        
        # 1. Bind Enter Key (Submit)
        # outputs=[query_box, chatbot] means:
        #   - 1st return value ("") -> goes to query_box (clearing it)
        #   - 2nd return value (history) -> goes to chatbot (updating it)
        query_box.submit(
            agent_chat,
            inputs=[query_box, chatbot],
            outputs=[query_box, chatbot],
        )
        
        # 2. Bind Click Button
        send_btn.click(
            agent_chat,
            inputs=[query_box, chatbot],
            outputs=[query_box, chatbot],
        )

    return demo