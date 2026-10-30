FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337
# Same pins as tests/Dockerfile (submission/tools/dev-requirements.lock); the agent's code runs in both images.
RUN pip install --no-cache-dir numpy==2.5.4 pandas==3.1.0 scipy==1.18.1 python-dateutil==3.0.0 six==1.17.0 tzdata==2026.6
WORKDIR /app
COPY app/ /app/
