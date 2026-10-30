FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337
# Same pins as environment/Dockerfile: the grader runs the agent's app and the untouched original with them.
RUN pip install --no-cache-dir \
    flask==3.1.3 werkzeug==3.1.9 jinja2==3.1.6 markupsafe==3.0.4 itsdangerous==2.2.0 click==8.5.0 blinker==1.9.0 \
    waitress==3.0.2 \
    pytest==9.2.0 iniconfig==2.3.1 packaging==26.3 pluggy==1.7.0 pygments==2.21.0
COPY . /tests/
RUN useradd -u 1001 -m runner && chmod 0700 /tests && chmod +x /tests/test.sh
WORKDIR /tests
