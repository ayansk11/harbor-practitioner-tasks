FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337
# Same pins as tests/Dockerfile (from submission/tools/dev-requirements.lock), every transitive dependency included.
RUN pip install --no-cache-dir numpy==2.5.4 pandas==3.1.0 python-dateutil==3.0.0 six==1.17.0 tzdata==2026.6 pyarrow==26.0.0 scikit-learn==1.9.1 scipy==1.18.1 joblib==1.6.0 cloudpickle==3.1.2 threadpoolctl==3.7.0 narwhals==2.28.0
WORKDIR /app
COPY app/ /app/
