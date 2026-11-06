FROM python:3.13-slim@sha256:09a17cad02668ae61ece136b4fd36ac3849e14f670ebedb637ea3e15580525bc
ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends git nodejs && rm -rf /var/lib/apt/lists/*
COPY trading_agent_starter/requirements.txt /requirements.txt
RUN python -m pip install --no-cache-dir -r /requirements.txt
COPY . /app
WORKDIR /app/trading_agent_starter
USER 65534:65534
ENTRYPOINT ["python", "/app/tools/iqp1_offline.py"]
