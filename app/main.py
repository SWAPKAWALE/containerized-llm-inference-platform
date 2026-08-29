import json
import os
import time

import requests
import streamlit as st


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:1b")


st.set_page_config(
    page_title="LLM Inference Platform",
    page_icon="🤖",
    layout="wide",
)


# -----------------------------
# Session state
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

if "last_latency" not in st.session_state:
    st.session_state.last_latency = 0.0


# -----------------------------
# Ollama functions
# -----------------------------

def check_ollama_health():
    try:
        response = requests.get(
            f"{OLLAMA_HOST}/api/tags",
            timeout=3,
        )

        return response.status_code == 200

    except requests.RequestException:
        return False


def stream_ollama_response(messages, temperature):
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": True,
            "keep_alive": "10m",
            "options": {
                "temperature": temperature,
                "num_predict": 256,
            },
        },
        stream=True,
        timeout=(5, 300),
    )

    response.raise_for_status()

    for line in response.iter_lines():

        if not line:
            continue

        data = json.loads(line.decode("utf-8"))

        if "message" in data:
            content = data["message"].get("content", "")

            if content:
                yield content


# -----------------------------
# Sidebar
# -----------------------------

with st.sidebar:

    st.header("⚙️ Inference Controls")

    server_online = check_ollama_health()

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


# -----------------------------
# Main interface
# -----------------------------

st.title("🤖 Containerized LLM Inference Platform")

st.caption(
    "Self-hosted GPU-accelerated LLM inference "
    "using Ollama, Streamlit and Docker"
)

st.divider()


# Display previous messages

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -----------------------------
# User input
# -----------------------------

prompt = st.chat_input(
    "Ask your local LLM anything..."
)


if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)


    if not check_ollama_health():

        st.error(
            "Ollama inference server is unavailable."
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

                for chunk in stream_ollama_response(
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

                st.session_state.last_latency = latencygit add app .gitignore


            except requests.RequestException as error:

                st.error(
                    f"Inference request failed: {error}"
                )