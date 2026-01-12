package main

import (
	"context"
	"fmt"
	"net/http"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/kelseyhightower/envconfig"
	"github.com/rs/zerolog/log"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	gw "github.com/abayleypublic/queue/gateway/gen/go/proto"
)

type Config struct {
	Backend string `envconfig:"backend" default:"localhost:8001"`
	Port    int    `envconfig:"port" default:"8004"`
}

func CustomMatcher(key string) (string, bool) {
	switch key {
	case "X-Auth-Request-User":
		return key, true
	case "X-Auth-Request-Email":
		return key, true
	case "X-Auth-Request-Groups":
		return key, true
	default:
		// Also handle tracing headers
		switch strings.ToLower(key) {
		case "traceparent", "tracestate":
			return key, true
		default:
			return runtime.DefaultHeaderMatcher(key)
		}
	}
}

func main() {
	var cfg Config
	if err := envconfig.Process("gateway_", &cfg); err != nil {
		log.Fatal().Err(err).Msg("failed to process config")
	}

	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	otel.SetTextMapPropagator(propagation.TraceContext{})

	mux := runtime.NewServeMux(
		runtime.WithIncomingHeaderMatcher(CustomMatcher),
	)
	opts := []grpc.DialOption{
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithStatsHandler(otelgrpc.NewClientHandler()),
	}
	if err := gw.RegisterQueueHandlerFromEndpoint(ctx, mux, cfg.Backend, opts); err != nil {
		log.Fatal().Err(err).Msg("failed to register gateway handler")
	}

	log.Info().Str("backend", cfg.Backend).Int("port", cfg.Port).Msg("starting gateway")
	if err := http.ListenAndServe(fmt.Sprintf(":%d", cfg.Port), mux); err != nil {
		log.Fatal().Err(err).Msg("failed to start gateway")
	}
}
