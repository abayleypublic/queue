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

	gw "github.com/abayleypublic/queue/gateway/gen/go"
)

type Config struct {
	Backend string `envconfig:"BACKEND" default:"localhost:8001"`
	Port    int    `envconfig:"PORT" default:"8004"`
}

func main() {
	var cfg Config
	if err := envconfig.Process("", &cfg); err != nil {
		log.Fatal().Err(err).Msg("failed to process config")
	}

	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	mux := runtime.NewServeMux()
	opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
	if err := gw.RegisterQueueHandlerFromEndpoint(ctx, mux, cfg.Backend, opts); err != nil {
		log.Fatal().Err(err).Msg("failed to register gateway handler")
	}

	log.Info().Str("backend", cfg.Backend).Int("port", cfg.Port).Msg("starting gateway")
	if err := http.ListenAndServe(fmt.Sprintf(":%d", cfg.Port), mux); err != nil {
		log.Fatal().Err(err).Msg("failed to start gateway")
	}
}
