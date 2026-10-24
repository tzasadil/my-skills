---
name: docker-best-practices
description: Use when writing, reviewing, or nontrivially changing a Dockerfile, a compose.yaml service, or a GitHub Actions image build.
---

# Docker Best Practices

## Layer order

Layers build top to bottom. One changed layer invalidates every layer below. Least-changing first:

1. OS packages (`apt-get install`)
2. Dependencies, gated on the lockfile (`COPY package.json pnpm-lock.yaml ./` then `pnpm install --frozen-lockfile`)
3. Source (`COPY . .`)
4. Build output (`RUN pnpm run build`)

- Pair update, install, and cleanup in one `RUN`. Split `apt-get update` leaves a stale index: `RUN apt-get update && apt-get install -y --no-install-recommends <pkgs> && rm -rf /var/lib/apt/lists/*`
- Merge only steps that must share a layer (update + install, install + cleanup). Unrelated giant `RUN`s trade cache reuse for layer count.
- Copy the manifest and lockfile before install: `package.json` + `pnpm-lock.yaml`, `go.mod` + `go.sum`, `requirements.txt`, `pom.xml`.
- `pnpm install --frozen-lockfile` in images. Without it the lockfile can rewrite.
- `pnpm fetch` (lockfile-only layer, then `pnpm install --offline`) is not drop-in. On pnpm 10.33 with a real lockfile it failed twice: `ERR_PNPM_IGNORED_BUILDS` (build approvals live in `package.json`, which fetch never sees) and `ERR_PNPM_NO_OFFLINE_TARBALL`. Adopt only after a full build passes.
- Source-driven generators (Prisma client) after `COPY . .`, not during `pnpm install`. Global `--ignore-scripts` breaks other packages' install scripts.
- No `apt-get upgrade` in an image. Rebuild from a newer base.
- Pipes swallow failure: `curl -s url | tar xz` exits 0 when curl dies. Debian `/bin/sh` (dash) has no `pipefail`. Set it once per stage: `SHELL ["/bin/bash", "-o", "pipefail", "-c"]`. Alpine has no bash: use `/bin/sh` (busybox ash supports it). Side effect: `grep -q` or `head` at the end of a pipe can now fail the step with SIGPIPE. Still prefer download, checksum, then extract.
- Multi-line scripts: `RUN <<EOF` heredoc instead of long `&& \` chains.
- `ARG` before `FROM` is visible only in `FROM` lines. Redeclare `ARG NAME` inside the stage to use it.
- Changed `ARG` value invalidates from its first use down. Volatile args (`GIT_SHA`, `BUILD_DATE`) belong in the final stage, after installs. Earlier => every commit reinstalls deps.

## Multi-stage builds

Build where the toolchain lives. Ship from a stage that has none of it.

```dockerfile
# syntax=docker/dockerfile:1
FROM node:24.21-bookworm-slim AS base
# Store lives in $PNPM_HOME/store. Cache mounts target this path.
ENV PNPM_HOME=/pnpm
# Install pnpm once here. Keep in sync with `packageManager`: pnpm 10 switches to that version and downloads it otherwise.
RUN npm install -g pnpm@10.33.0
WORKDIR /app

FROM base AS deps
COPY package.json pnpm-lock.yaml ./
# Prod tree only. The runtime copies this. The build stage's node_modules includes compilers.
RUN pnpm install --prod --frozen-lockfile

FROM base AS build
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build

FROM node:24.21-bookworm-slim
ENV NODE_ENV=production
WORKDIR /app
# package.json: Node reads "type" from it to pick ESM vs CJS for dist/*.js.
COPY --chown=node:node package.json ./
COPY --link --chown=1000:1000 --from=deps /app/node_modules ./node_modules
COPY --link --chown=1000:1000 --from=build /app/dist ./dist
USER node
CMD ["node", "dist/server.js"]
```

- `--link` pays off when the runtime base differs from the build stages. Runtime base bump => links reuse the copied layers. Build stages that share the bumped base rebuild anyway.

- Absolute `WORKDIR` (`/app`, not `app`).
- Prod deps from their own stage. Single-stage ships compiler, caches, and unused source.
- Self-contained bundle (Next.js `output: 'standalone'`): copy bundle, static assets, `public`. Skip `node_modules` in runtime.
- pnpm via `npm install -g pnpm@<v>`, not `corepack enable`. Node 25+ images ship no corepack (`corepack: not found`). Existing corepack Dockerfiles on Node 22.11 or older (corepack below 0.31) fail pnpm downloads with `verifySignature` errors: bump Node or migrate.
- Native binaries between stages: match OS/libc/arch/ABI unless deliberately cross-building.
- One concern per container, not per image. Reuse one artifact with different `CMD`s for API vs worker. Cron-plus-app is two concerns.

## pnpm workspaces

Copy every manifest before installing, then scope the install. Dependency layer survives source edits in any member.

```dockerfile
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/api/package.json ./apps/api/
COPY packages/shared/package.json ./packages/shared/

RUN pnpm install --frozen-lockfile --filter api...
```

- `<pkg>...` includes workspace dependencies. Copying every member manifest is also fine: one dependency layer for every image from the repo.
- Runtime can `pnpm install --frozen-lockfile --filter <pkg>... --prod` from manifests instead of copying `node_modules` from build.
- Copy only that package's source (`COPY apps/api ./apps/api`). Repo-wide `COPY . .` invalidates on any sibling change.
- `pnpm --filter <pkg> deploy --prod /out` builds a pruned runtime tree (package + prod deps + linked workspace packages). pnpm 10 refuses with `ERR_PNPM_DEPLOY_NONINJECTED_WORKSPACE` unless the workspace sets `inject-workspace-packages=true` or the call adds `--legacy`.

## Build context and caches

- `.dockerignore` at the context root: the whole context is sent before the first instruction. Exclude `.git`, `node_modules`, `dist`, logs, local env. A plain `.dockerignore` next to a nested Dockerfile is ignored when context is repo root. `<Dockerfile-name>.dockerignore` beside that Dockerfile (`Dockerfile.dockerignore`, `api.Dockerfile.dockerignore`) takes precedence.
- Allowlist beats denylist: `*`, then `!package.json`, `!pnpm-lock.yaml`, `!apps/api/**`. New junk or secret files stay out by default.
- Do not `COPY . .` before the dependency install. Do not rely on host-generated artifacts unless the build contract says so.
- BuildKit cache mounts: `RUN --mount=type=cache,id=pnpm-store,target=/root/.local/share/pnpm/store pnpm install --frozen-lockfile`. Target must match where pnpm looks (`/root/.local/share/pnpm/store` without `PNPM_HOME`, or `$PNPM_HOME/store`). Build must succeed with an empty cache.
- Cache mount and `node_modules` sit on different filesystems: pnpm copies files instead of hardlinking (`stat -c %h` shows 1). Expected. Store stays out of the image layer.
- Apt cache mount stays empty by default: the base image's `docker-clean` config deletes `.deb`s after install. `RUN rm -f /etc/apt/apt.conf.d/docker-clean` first, then `--mount=type=cache,target=/var/cache/apt,sharing=locked` and `target=/var/lib/apt`.
- Manifests without a `COPY` layer: `RUN --mount=type=bind,source=package.json,target=package.json --mount=type=bind,source=pnpm-lock.yaml,target=pnpm-lock.yaml pnpm install --frozen-lockfile`. Cache still keys on file content. Files are absent afterward, so later steps that need them still `COPY`.
- Default `sharing=shared` is safe for pnpm (content-addressed, atomic rename). `sharing=locked` for exclusive caches (Apt). Recover a bad store: `docker buildx prune --filter type=exec.cachemount`.
- Clean in the layer that made the mess: `pip install --no-cache-dir`, `--no-install-recommends`, `DEBIAN_FRONTEND=noninteractive`, `apk add --no-cache`.
- `COPY --link` is independent of layers beneath it. Works without a `# syntax=` line on current BuildKit (tested Docker 29). The line only pins the frontend version, so add it for older builders. Skip when the destination is a symlink you need to follow. `--link` + `--chown` needs numeric IDs (`--chown=1000:1000`): the linked layer has no `/etc/passwd`, so names fail with `invalid user index: -1`.
- `COPY --chown=node:node --chmod=755` sets owner and mode in the same layer. A later `RUN chown -R` / `chmod -R` copies every file into a new layer (50 MB file: 424 MB vs 524 MB image).
- Cache mounts are builder state, not image layers. `--cache-to`/`--cache-from` never carry them. Fresh CI runner = empty mount even on a layer-cache hit. Persist via `buildkit-cache-dance` or a persistent builder.

## CI builds (GitHub Actions)

GitHub-hosted runners are cold. Default `docker` driver cannot export cache. Store cache in the same registry as the images. `ref` tag is scope: one per image, target, and platform.

```yaml
- uses: docker/setup-buildx-action@v4
- uses: docker/login-action@v4
  with:
    registry: ${{ vars.REGISTRY_URL }}
    username: ${{ secrets.REGISTRY_USERNAME }}
    password: ${{ secrets.REGISTRY_PASSWORD }}
- uses: docker/metadata-action@v6
  id: meta
  with:
    images: ${{ vars.REGISTRY_URL }}/api
    tags: type=sha
- uses: docker/build-push-action@v7
  with:
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
    cache-from: type=registry,ref=${{ vars.REGISTRY_URL }}/api:buildcache-amd64
    cache-to: type=registry,ref=${{ vars.REGISTRY_URL }}/api:buildcache-amd64,mode=max
```

- `mode=max` exports intermediate stages. Default `min` only final-stage layers => multi-stage `deps`/`build` reruns. `max` costs cache pushes and registry storage.
- Registry cache survives branches and runners, ignores Actions cache quota. Keep cache tag distinct from image tag. `type=inline` carries only final-stage layers in the pushed image.
- Cache export happens after image push. Failed export fails an otherwise good build. `cache-to: ...,ignore-error=true` makes it non-fatal.
- ECR and some other registries reject the default cache manifest list. Add `image-manifest=true,oci-mediatypes=true` to `cache-to`.
- `provenance` defaults to `mode=min`: the pushed manifest list gains `unknown/unknown` attestation entries. Registries or tools that choke on them -> `provenance: false`. Supply-chain policy -> `sbom: true` + `provenance: mode=max`.
- Multi-platform on native runners: one job per platform pushes by digest (`outputs: type=image,push-by-digest=true,name-canonical=true,push=true`), a final job merges with `docker buildx imagetools create`.
- `type=gha` when the job cannot log in to the registry (fork PRs). Lives in Actions cache: branch-scoped, 10 GB/repo shared with `actions/cache`, evicted by last access, read-only on low-trust triggers (`pull_request_target`, `issue_comment`, `workflow_run`) where `cache-to` fails with `failed to reserve cache`.
- `type=gha` `scope` defaults to `buildkit`. Give each image, target, and matrix leg its own. Warm PRs from a trusted `push` to the default branch.
- Stale Docker Hub creds in `DOCKER_AUTH_CONFIG` / `~/.docker/config.json` break bootstrap: `docker-container` driver pulls `moby/buildkit` from Hub and 401s. Clear the Hub entry before `setup-buildx-action` when the job only talks to another registry.

## Base images

- Versioned tag, not `:latest`: `node:24-bookworm-slim`. Pin by digest only when policy requires it, and automate digest updates.
- Publish with git SHA or release version, not `:latest`.
- Prefer `-slim` for glibc/native Node. Alpine only after musl/native modules actually work. Do not add `libc6-compat` blindly.
- Distroless / Chainguard runtime bases (`gcr.io/distroless/nodejs22-debian12`): no shell, no package manager. Healthchecks, wrappers, and `CMD` must run without `/bin/sh`.
- Build the platforms you ship. Prefer native builders over emulation when speed or compiler behavior matters.

## Runtime

- Prod images run non-root: `USER node` after installs, `COPY --chown=node:node`. Non-root cannot write root-owned paths (`WORKDIR`, a named volume mounted on a path the image lacks) => `EACCES` at runtime. `mkdir` + `chown` every writable path (logs, cache, uploads) in the image, before `USER`. Docker 20.10+ lets non-root bind ports below 1024 (`ip_unprivileged_port_start=0`). Kubernetes does not by default. Dev images with bind mounts may stay root: host UID rarely matches `node`.
- `CMD ["node", ...]` in prod, not `pnpm run start` / `npm run start`. As PID 1 the package manager gets `SIGTERM` and exits without running the app's shutdown handler (pnpm 10: handler skipped, exit 1). Dev watch commands are exempt.
- JSON/exec form so signals reach the app, not `/bin/sh -c`. `CMD` for the normal command. `ENTRYPOINT` when the image is a wrapper and `CMD` supplies default args.
- Shell wrappers end with `exec "$@"`. PID 1 must reap: `exec "$@"` or tiny init (`tini`, Compose `init: true`). Do not add tini to a well-behaved PID 1.
- PID 1 gets no default signal handlers. Node as PID 1 without a `SIGTERM` handler ignores `SIGTERM` => killed after the grace period. Register a handler or run under an init.
- Handle `SIGTERM` within the platform stop timeout (Compose `stop_grace_period`, default 10 s).
- `EXPOSE` is documentation only. Update it when the listen port changes.
- Log to stdout/stderr. Writable state in a volume, not a layer.
- Dev images: bind mounts missing inotify events (mostly Docker Desktop file sharing, native Linux is fine) -> per-tool polling: `CHOKIDAR_USEPOLLING=true` (chokidar), `WATCHPACK_POLLING=true` (webpack, Next.js), `TSC_WATCHFILE=DynamicPriorityPolling` (`tsc`).

## Secrets

- `RUN --mount=type=secret,id=token`. `ARG`/`ENV` are in image config and `docker history`.
- Token as env for one step: `RUN --mount=type=secret,id=npm_token,env=NPM_TOKEN pnpm install` (Dockerfile syntax 1.10+) with `.npmrc` containing `//registry.npmjs.org/:_authToken=${NPM_TOKEN}`.
- Private git deps: `RUN --mount=type=ssh`, build with `--ssh default`.
- Never `COPY` `.env`, keys, or credentials. `.dockerignore` them.
- Runtime secrets as env or mounted files at start, not baked at build.
- A secret copied in any stage stays in that stage's layers. The final image omits them, but `--target <stage>` images and `cache-to mode=max` exports carry them.

## Compose

Project name is part of every image tag and named volume. Defaults to the basename of the project directory = directory of the first `-f` file, not the shell cwd. `-f deployment/compose.yaml` -> project `deployment`.

- `.env` next to that first file feeds `${VAR}` interpolation in the compose file. `env_file:` injects variables into the container. Different jobs, often confused.

- Pin `name:` / `-p` / `COMPOSE_PROJECT_NAME` when several invocations should share one stack. Unique names for worktrees and CI are intentional.
- `image: <repo>-<service>:local` next to `build:` for a stable local tag across project-name changes.
- One Dockerfile for dev and prod: named stages + `build.target: dev`.
- Several images from one repo: `docker buildx bake` (or `COMPOSE_BAKE=true` for `compose build`) builds them in parallel with shared context and cache.
- Avoid `container_name` unless an external tool requires that exact name. Blocks scaling and parallel projects.
- Prefer no `node_modules` mount when selective source/config bind mounts leave image-installed deps visible. A mount hides updated image deps after rebuild.
- Named volumes in top-level `volumes:`, not anonymous (`- /app/node_modules`). Anonymous volumes leak if you `down` without `-v`.
- Named-volume deps go stale when the lockfile changes. Dev entrypoint can rerun the filtered install and `exec "$@"` at start.
- `init: true` runs bundled tini when the process tree needs reaping.
- `depends_on` short form waits for start, not ready. Long form: `condition: service_healthy` (needs a `HEALTHCHECK`), `service_completed_successfully` (one-shot migrate/bootstrap), `restart: true` (dependent restarts when compose restarts the dependency), `required: false` (dependency in an inactive profile does not block). The app still retries transients after it is up.
- Healthcheck timing: `start_period` ignores failures during boot, `start_interval` (Docker Engine 25+) sets the poll rate inside it. `interval: 30s` + `start_interval: 1s` reports healthy about 1 s after ready, not up to 30 s.
- `docker compose up -d --wait` blocks until services are running/healthy. Use in CI and scripts instead of `sleep`.
- Dev service that compiles at start (`nest start --watch`, webpack): no blocking `depends_on`. Compile overlaps DB startup. Gate only the run step: `--exec` wrapper polls a gate service that has the real `depends_on` conditions and opens a port once ready.
  - Gate: `busybox:1.37`, `entrypoint: ["nc", "-ll", "-p", "8080", "-e", "true"]`, same network as the app => hostname resolves.
  - Wrapper probe needs a tool in the app image. `/bin/sh` has no `/dev/tcp` (Alpine ash, Debian dash) => loop never ends. Alpine: `until nc -z -w 1 <gate> 8080; do sleep 1; done; exec node "$@"`. Debian slim (no `nc`): `#!/bin/bash` + `until (exec 3<>/dev/tcp/<gate>/8080) 2>/dev/null; ...`.
  - Base file shared with prod (prod keeps blocking `depends_on`) -> dev overlay `depends_on: !reset {}` (Compose 2.24+). Merge only adds keys. App `depends_on` the gate => serial again.
- Required settings: `${VAR:?message}` so a missing value fails start with a readable error.
- Healthchecks use tools in the image. Alpine has busybox `wget`, not `curl`: `wget -q --spider http://127.0.0.1:<port>/`. Debian `-slim` has neither: `node -e "fetch('http://127.0.0.1:<port>/').then(r=>process.exit(r.ok?0:1),()=>process.exit(1))"`.
- Dev sync: `develop.watch` (Compose 2.22+, `sync+restart` 2.23+, `sync+exec` 2.32+) instead of bind mounts. `sync` for source, `ignore: [node_modules/]`, `rebuild` for lockfile and manifest changes. Run `docker compose watch` or `up --watch`. A non-root container needs the target writable: `COPY --chown`, else sync fails.
- Publish only host ports humans or external systems need. Same-network services talk by service name.

## Verification

Non-trivial change: `docker build -f <Dockerfile> <context>` and `docker compose config`. `docker build --check` lints (including style). A warning is a lead, not proof the change is wrong. Run the service far enough to see startup, signals, and required files. Caching change: build log must show cache import/export; a second run must report `CACHED` for unchanged layers. A green first run proves nothing.
