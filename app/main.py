import logging
import os
import time

import requests
import streamlit as st

from ollama_client import (
    check_health,
    model_available,
    stream_chat,
)


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434",
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "llama3.2:1b",
)


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
# Service status
# --------------------------------------------------

server_online = check_health(OLLAMA_HOST)

model_ready = (
    model_available(
        OLLAMA_HOST,
        MODEL_NAME,
    )
    if server_online
    else False
)


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:

    st.header("⚙️ Inference Controls")

    if server_online:
        st.success("Ollama Server: Online")
    else:
        st.error("Ollama Server: Offline")

    if model_ready:
        st.success("Model: Ready")
    elif server_online:
        st.warning("Model: Not Available")

    st.write("**Active Model**")
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

        logger.info("Chat history cleared.")

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
# Display conversation history
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

    logger.info("New user inference request received.")

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)


    if not server_online:

        logger.error(
            "Inference rejected because Ollama is offline."
        )

        st.error(
            "Ollama inference server is unavailable."
        )


    elif not model_ready:

        logger.error(
            "Inference rejected because model %s is unavailable.",
            MODEL_NAME,
        )

        st.error(
            f"Model '{MODEL_NAME}' is not available."
        )


    else:

        with st.chat_message("assistant"):

            placeholder = st.empty()

            full_response = ""

            start_time = time.time()

            try:

                api_messages = [
                    {
                        "role": message["role"],
                        "content": message["content"],
                    }
                    for message in st.session_state.messages
                ]


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


                latency = time.time() - start_time


                placeholder.markdown(
                    full_response
                )

                st.caption(
                    f"Response time: {latency:.2f}s"
                )


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": full_response,
                    }
                )


                st.session_state.request_count += 1

                st.session_state.last_latency = latency


                logger.info(
                    "Inference completed successfully in %.2f seconds.",
                    latency,
                )


            except requests.RequestException as error:

                logger.exception(
                    "Inference request failed."
                )

                st.error(
                    f"Inference request failed: {error}"
                )