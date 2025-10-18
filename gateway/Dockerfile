FROM golang:1.25.2-alpine3.22

ARG TARGETOS TARGETARCH TARGETVARIANT

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN GOOS=$TARGETOS GOARCH=$TARGETARCH GOARM=${TARGETVARIANT#v} CGO_ENABLED=0 go build -o /gateway ./main.go

ENTRYPOINT ["/gateway"]