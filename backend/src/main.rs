#![warn(unused_extern_crates)]

mod api;
mod user;

use api::middleware::auth_interceptor;
use api::queue::queue::queue_server::QueueServer;
use http::Request;
use opentelemetry::trace::TracerProvider;
use opentelemetry::{global, propagation::Extractor};
use opentelemetry_sdk::{propagation::TraceContextPropagator, trace::SdkTracerProvider};
use serde::Deserialize;
use tonic::{service::interceptor::InterceptedService, transport::Server};
use tower_http::trace::TraceLayer;
use tracing::{error, info};
use tracing_opentelemetry::OpenTelemetrySpanExt;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

pub mod proto {
    pub(crate) const FILE_DESCRIPTOR_SET: &[u8] =
        tonic::include_file_descriptor_set!("queue_descriptor");
}

#[derive(Deserialize, Debug)]
struct Config {
    #[serde(default = "default_address")]
    address: String,

    #[serde(default = "default_redis_url")]
    redis_url: String,
}

fn default_address() -> String {
    "[::1]:8001".to_string()
}

fn default_redis_url() -> String {
    "redis://127.0.0.1/".to_string()
}

fn init_tracing() -> Result<(), Box<dyn std::error::Error>> {
    global::set_text_map_propagator(TraceContextPropagator::new());

    let provider = SdkTracerProvider::builder().build();
    let tracer = provider.tracer("backend");
    global::set_tracer_provider(provider);

    let env_filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| "info,tower_http=info,tonic=info".into());

    tracing_subscriber::registry()
        .with(env_filter)
        .with(tracing_subscriber::fmt::layer())
        .with(tracing_opentelemetry::layer().with_tracer(tracer))
        .init();

    Ok(())
}

struct HeaderExtractor<'a>(&'a http::HeaderMap);
impl<'a> Extractor for HeaderExtractor<'a> {
    fn get(&self, key: &str) -> Option<&str> {
        self.0.get(key)?.to_str().ok()
    }
    fn keys(&self) -> Vec<&str> {
        self.0.keys().map(|k| k.as_str()).collect()
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    init_tracing()?;

    let cfg = match envy::prefixed("BACKEND_").from_env::<Config>() {
        Ok(config) => config,
        Err(error) => {
            error!("configuration error: {}", error);
            std::process::exit(1);
        }
    };

    let client = redis::Client::open(cfg.redis_url).unwrap();
    let redis_connection = client.get_multiplexed_async_connection().await.unwrap();

    let queue_service = api::queue::QueueService::new(redis_connection);

    let reflection_service = tonic_reflection::server::Builder::configure()
        .register_encoded_file_descriptor_set(proto::FILE_DESCRIPTOR_SET)
        .build_v1alpha()
        .unwrap();

    let addr = cfg.address.parse()?;
    info!("starting server on {}", cfg.address);

    let grpc_trace = TraceLayer::new_for_grpc().make_span_with(|req: &Request<_>| {
        let parent_cx =
            global::get_text_map_propagator(|p| p.extract(&HeaderExtractor(req.headers())));

        let span = tracing::info_span!(
            "rpc.server",
            otel.name = %req.uri().path(),
            otel.kind = "server",
            "rpc.system" = "grpc",
            "rpc.service" = "queue.Queue",
            "rpc.method" = %req.uri().path(),
        );

        span.set_parent(parent_cx);
        span
    });

    let svc = QueueServer::new(queue_service);
    let intercepted_svc = InterceptedService::new(svc, auth_interceptor);

    Server::builder()
        .layer(grpc_trace)
        .add_service(intercepted_svc)
        .add_service(reflection_service)
        .serve(addr)
        .await?;

    Ok(())
}
