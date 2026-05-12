# syntax=docker/dockerfile:1.7
#
# eme-gir — Sumerian dictionary + corpus + MCP server, packaged as one
# image that runs two services in compose: gunicorn-fronted Flask web
# (port 5050) and the MCP server in HTTP transport (port 5051).
#
# corpus/, data/, log/ are bind-mounted from the host at runtime — they
# total ~6 GB and would be both prohibitively large to bake in and
# pointless to ship (anyone using this image will have built their own
# indexes locally; see README "Setup" for the build sequence).

FROM python:3.12.11-slim

# `ijson` ships a fast yajl2-C backend that the build_*.py scripts rely
# on for constant-memory streaming JSON parses; install the C library
# so the wheel picks it up. (Without libyajl2, ijson silently falls
# back to its slow pure-python parser — same correctness, ~10x slower.)
# `curl` is for healthchecks; ~5 MB and avoids hand-rolling urllib in
# every check spec.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libyajl2 curl \
    && rm -rf /var/lib/apt/lists/*

# Run as a non-root user. uid/gid 1000 matches the conventional first
# user on most Linux hosts, so bind-mounted host directories are
# writable without a chown dance. Override with `user:` in compose if
# your host user has a different uid (Linux: `id -u`; macOS Docker
# Desktop already maps host owners through to the container, so the
# uid in here doesn't matter much).
RUN groupadd --system --gid 1000 eme-gir \
    && useradd  --system --uid 1000 --gid eme-gir --home-dir /app --shell /usr/sbin/nologin eme-gir

WORKDIR /app

# Reserved for future use — currently every dep in requirements.txt
# is on public PyPI, so the token isn't consumed. If/when we add a
# private package hosted on the Forgejo PyPI registry, wire it into
# pip via:
#   RUN pip install --no-cache-dir \
#         --extra-index-url "https://__token__:${FORGEJO_AUTH_TOKEN}@git.rso/api/packages/trex/pypi/simple/" \
#         -r requirements.txt
# Declaring the ARG here (even when unused) lets the CI workflow pass
# --build-arg FORGEJO_AUTH_TOKEN=... without emitting a "build arg not
# consumed" warning, and makes the extension point obvious.
ARG FORGEJO_AUTH_TOKEN=""

# Deps first so source-only changes don't bust the layer cache.
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Then the source. Excludes are in .dockerignore — corpus/, data/,
# log/, .git/, etc. are NOT copied; they come from bind mounts.
COPY --chown=eme-gir:eme-gir . /app/

# Pre-create writable dirs AND chown /app itself. WORKDIR /app makes
# the directory root-owned; COPY --chown only chowns copied files,
# not the parent. Without this, gunicorn (running as eme-gir) can't
# create its control file at /app/.gunicorn and crashes on boot with
# "Control server error: [Errno 13] Permission denied".
# init.sh needs +x (the COPY may not preserve host perms); doing it
# here means the `init` compose service can run it directly.
RUN install -d -o eme-gir -g eme-gir /app/data /app/log \
    && chown eme-gir:eme-gir /app \
    && chmod +x /app/init.sh

USER eme-gir

# Both services listen on these ports inside the container; compose
# decides what to publish on the host (default: 127.0.0.1 only, so
# nothing is exposed beyond localhost without a reverse proxy).
EXPOSE 5050 5051

# No CMD — services pick their own command in docker-compose.yml.
# Run directly: `docker run --rm eme-gir python3 mcp_server.py --help`.
