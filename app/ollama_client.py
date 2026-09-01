import json

import requests


def check_health(ollama_host):
    try:
        response = requests.get(
            f"{ollama_host}/api/tags",
            timeout=3,
        )
        return response.status_code == 200

    except requests.RequestException:
        return False


def stream_chat(
    ollama_host,
    model_name,
    messages,
    temperature=0.7,
):
    response = requests.post(
        f"{ollama_host}/api/chat",
        json={
            "model": model_name,
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

        data = json.loads(
            line.decode("utf-8")
        )

        content = (
            data.get("message", {})
            .get("content", "")
        )

        if content:
            yield content