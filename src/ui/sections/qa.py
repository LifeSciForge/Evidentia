"""
MSL Tab: Ask Evidentia Q&A Chat section (rendering wrapper only).

LLM logic lives in src/service/qa_service.py.
Moved from src/ui/app.py as part of Stage 5 — Architecture Refactor (Part 2).
"""

import streamlit as st
from src.service.qa_service import generate_qa_answer


def display_qa_chat_section(state):
    """Interactive Q&A chat interface for MSL questions"""

    st.subheader("💬 Ask Evidentia")
    st.markdown("*Ask natural language questions about your brief*")

    # Display chat history
    chat_history = st.session_state.get("chat_history", [])
    if chat_history:
        st.write("**Conversation:**")
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.write(f"**You:** {message['content']}")
            else:
                st.write(f"**Evidentia:** {message['content']}")
            st.markdown("---")

    st.markdown("---")

    # Input form to prevent duplicate submissions
    with st.form(key="qa_form", clear_on_submit=True):
        user_question = st.text_input(
            "Ask a question about your brief:",
            placeholder="e.g., What if the doctor asks about side effects?",
            key="qa_input"
        )

        submit_button = st.form_submit_button("📤 Send Question")

    if submit_button and user_question:
        # Add user question to history
        chat_history = st.session_state.get("chat_history", [])
        chat_history.append({
            'role': 'user',
            'content': user_question
        })
        st.session_state.chat_history = chat_history

        # Generate answer based on brief data
        answer = generate_qa_answer(user_question, state)

        # Add answer to history
        chat_history = st.session_state.get("chat_history", [])
        chat_history.append({
            'role': 'assistant',
            'content': answer
        })
        st.session_state.chat_history = chat_history

        # Rerun to display new message (but form is cleared)
        st.rerun()

    # Clear chat button (moved outside form)
    st.markdown("---")
    chat_history = st.session_state.get("chat_history", [])
    if chat_history:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
                st.rerun()
