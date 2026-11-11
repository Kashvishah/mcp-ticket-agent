import asyncio

import streamlit as st

from agent import ask_agent, confirm_create_ticket

st.title("Ticket Agent")
st.caption("Ask a question about the support tickets.")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_create" not in st.session_state:
    st.session_state.pending_create = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input("Ask about your tickets"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    try:
        with st.spinner("Checking the tickets..."):
            result = asyncio.run(ask_agent(question, st.session_state.messages[:-1]))
        if "pending" in result:
            st.session_state.pending_create = result["pending"]
        else:
            st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
            with st.chat_message("assistant"):
                st.markdown(result["answer"])
    except Exception as error:
        message = f"I couldn't get an answer: {error}"
        st.session_state.messages.append({"role": "assistant", "content": message})
        with st.chat_message("assistant"):
            st.error(message)

if st.session_state.pending_create:
    pending = st.session_state.pending_create
    with st.chat_message("assistant"):
        st.write("The agent wants to create this ticket. Confirm before it is saved:")
        st.json(pending["arguments"])
        confirm, cancel = st.columns(2)
        if confirm.button("Confirm and create", key="confirm_create_ticket"):
            try:
                with st.spinner("Creating the ticket..."):
                    result = asyncio.run(confirm_create_ticket(pending))
                st.session_state.pending_create = result.get("pending")
                if "answer" in result:
                    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
            except Exception as error:
                st.session_state.pending_create = None
                st.session_state.messages.append({"role": "assistant", "content": f"Ticket creation failed: {error}"})
            st.rerun()
        if cancel.button("Cancel", key="cancel_create_ticket"):
            st.session_state.pending_create = None
            st.session_state.messages.append(
                {"role": "assistant", "content": "Ticket creation cancelled; nothing was saved."}
            )
            st.rerun()
