import os
import time

import requests
import streamlit as st

from ollama_client import check_health, stream_chat


OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434",
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "llama3.2:1b",
)


# --------------------------------------------------
# Streamlit page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="LLM Inference Platform",
    page_icon="🤖",
    layout="wide",
)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

if "last_latency" not in st.session_state:
    st.session_state.last_latency = 0.0


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:

    st.header("⚙️ Inference Controls")

    server_online = check_health(OLLAMA_HOST)

    if server_online:
        st.success("Server Online")
    else:
        st.error("Server Offline")

    st.write("**Model**")
    st.code(MODEL_NAME)

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
    )

    st.divider()

    st.metric(
        "Requests",
        st.session_state.request_count,
    )

    st.metric(
        "Last Response",
        f"{st.session_state.last_latency:.2f}s",
    )

    if st.button(
        "Clear Chat",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.session_state.request_count = 0
        st.session_state.last_latency = 0.0

        st.rerun()


# --------------------------------------------------
# Main interface
# --------------------------------------------------

st.title("🤖 Containerized LLM Inference Platform")

st.caption(
    "Self-hosted GPU-accelerated LLM inference "
    "using Ollama, Streamlit and Docker"
)

st.divider()


# --------------------------------------------------
# Display chat history
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------------------------
# User input
# --------------------------------------------------

prompt = st.chat_input(
    "Ask your local LLM anything..."
)


if prompt:

    # Save user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)


    # Check Ollama availability
    if not check_health(OLLAMA_HOST):

        st.error(
            "Ollama inference server is unavailable."
        )

    else:

        # Display assistant response
        with st.chat_message("assistant"):

            placeholder = st.empty()

            full_response = ""

            start_time = time.time()

            try:

                # Prepare complete conversation history
                api_messages = [
                    {
                        "role": message["role"],
                        "content": message["content"],
                    }
                    for message in st.session_state.messages
                ]

                # Stream response from Ollama
                for chunk in stream_chat(
                    OLLAMA_HOST,
                    MODEL_NAME,
                    api_messages,
                    temperature,
                ):

                    full_response += chunk

                    placeholder.markdown(
                        full_response + "▌"
                    )


                # Calculate response latency
                latency = time.time() - start_time


                # Display completed response
                placeholder.markdown(
                    full_response
                )

                st.caption(
                    f"Response time: {latency:.2f}s"
                )


                # Save assistant response
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": full_response,
                    }
                )


                # Update metrics
                st.session_state.request_count += 1

                st.session_state.last_latency = latency


            except requests.RequestException as error:

                st.error(
                    f"Inference request failed: {error}"
                )