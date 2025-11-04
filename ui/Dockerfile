FROM node:24.7.0-slim AS build
ARG TARGETOS TARGETARCH
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

RUN corepack enable

WORKDIR /app

COPY package.json pnpm-lock.yaml ./

RUN case "${TARGETARCH}" in \
    amd64) pnpm add -D @rolldown/binding-linux-x64-gnu ;; \
    arm64) pnpm add -D @rolldown/binding-linux-arm64-gnu ;; \
    *) echo "Unsupported arch: ${TARGETARCH}" && exit 1 ;; \
    esac

RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile

COPY . .
RUN pnpm run build

FROM nginx:1.29.3-alpine3.22
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
