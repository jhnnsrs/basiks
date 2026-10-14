FROM python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv

RUN mkdir /app
WORKDIR /app

# Outside /app, so copying the project below cannot replace it with a host .venv.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

ENV PATH="/opt/venv/bin:$PATH"

# The whole project: the app target may be any module in it, not only app.py.
COPY . /app

# Bake the scikit-image sample data in, so Generate Test Image works offline
RUN python init.py

# The version of this build, when it is not the one the source declares: a build from
# a branch is passed it by `arkitekt plugin release`. Empty for a release proper. Last,
# so a new version does not re-run the steps above.
ARG ARKITEKT_APP_VERSION=""
ENV ARKITEKT_APP_VERSION=$ARKITEKT_APP_VERSION
