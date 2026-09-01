import json
import logging

import requests


logger = logging.getLogger(__name__)


def check_health(ollama_host):
    try:
        response = requests.get(
            f"{ollama_host}/api/tags",
            timeout=3,
        )

        if response.status_code == 200:
            logger.info("Ollama server health check successful.")
            return True

        logger.warning(
            "Ollama health check returned status %s.",
            response.status_code,
        )

        return False

    except requests.RequestException as error:
        logger.error(
            "Unable to connect to Ollama: %s",
            error,
        )

        return False


def model_available(
    ollama_host,
    model_name,
):
    try:
        response = requests.get(
            f"{ollama_host}/api/tags",
            timeout=3,
        )

        response.raise_for_status()

        models = response.json().get(
            "models",
            [],
        )

        available_models = [
            model.get("name")
            for model in models
        ]

        is_available = (
            model_name in available_models
        )

        if is_available:
            logger.info(
                "Model %s is available.",
                model_name,
            )
        else:
            logger.warning(
                "Model %s is not available.",
                model_name,
            )

        return is_available

    except requests.RequestException as error:
        logger.error(
            "Failed to retrieve model list: %s",
            error,
        )

        return False


def stream_chat(
    ollama_host,
    model_name,
    messages,
    temperature=0.7,
):
    logger.info(
        "Starting inference request using model %s.",
        model_name,
    )

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

        try:
            data = json.loads(
                line.decode("utf-8")
            )

        except json.JSONDecodeError:
            logger.warning(
                "Received invalid JSON from Ollama."
            )
            continue

        content = (
            data.get("message", {})
            .get("content", "")
        )

        if content:
            yield content

    logger.info(
        "Inference request completed."
    )