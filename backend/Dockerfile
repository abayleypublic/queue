FROM rust:1.89.0 as build

ARG TARGETARCH

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends --assume-yes \
    protobuf-compiler \
    libprotobuf-dev

COPY ./backend ./app
COPY ./proto ./proto

WORKDIR /app

RUN set -eux; \
    if [ "$TARGETARCH" = "amd64" ]; then \
    rustup target add x86_64-unknown-linux-musl; \
    export RUST_TARGET="x86_64-unknown-linux-musl"; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
    rustup target add aarch64-unknown-linux-musl; \
    export RUST_TARGET="aarch64-unknown-linux-musl"; \
    else \
    echo "unsupported architecture: $TARGETARCH"; exit 1; \
    fi; \
    cargo build --release --target $RUST_TARGET; \
    cp target/$RUST_TARGET/release/backend /backend

FROM scratch
WORKDIR /

COPY --from=build /backend /backend

ENTRYPOINT ["/backend"]
