FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337
# Same pins as environment/Dockerfile: the grader runs the agent's pipeline here as uid 1001.
RUN pip install --no-cache-dir numpy==2.5.4 pandas==3.1.0 python-dateutil==3.0.0 six==1.17.0 tzdata==2026.6 pyyaml==6.0.3
COPY . /tests/
RUN useradd -u 1001 -m runner && chmod 0700 /tests && chmod +x /tests/test.sh
WORKDIR /tests
