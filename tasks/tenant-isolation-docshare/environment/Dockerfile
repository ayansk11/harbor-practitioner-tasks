FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337
# Exact pins from submission/tools/dev-requirements.lock (Flask and its dependencies, waitress, pytest and its
# dependencies); tests/Dockerfile installs the same list.
RUN pip install --no-cache-dir \
    flask==3.1.3 werkzeug==3.1.9 jinja2==3.1.6 markupsafe==3.0.4 itsdangerous==2.2.0 click==8.5.0 blinker==1.9.0 \
    waitress==3.0.2 \
    pytest==9.2.0 iniconfig==2.3.1 packaging==26.3 pluggy==1.7.0 pygments==2.21.0
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY app/ /app/
