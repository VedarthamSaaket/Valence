FROM python:3.11-slim

# llama-cpp-python ships prebuilt CPU wheels; build tools are a fallback in
# case the wheel index misses this platform.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu \
    && pip install --no-cache-dir fastapi uvicorn huggingface_hub pydantic

# Spaces run the container as uid 1000 with $HOME unset-ish; keep caches local.
ENV HOME=/app \
    HF_HOME=/app/.cache/huggingface

RUN mkdir -p /app/.cache/huggingface && chmod -R 777 /app

COPY app.py /app/app.py

EXPOSE 7860
CMD ["python", "app.py"]
