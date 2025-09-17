#![warn(unused_extern_crates)]

mod service;

use serde::Deserialize;
use tonic::transport::Server;
use tower_http::trace::TraceLayer;
use tracing::{error, info};
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
    let env_filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| "info,tower_http=info,tonic=info".into());

    tracing_subscriber::registry()
        .with(env_filter)
        .with(tracing_subscriber::fmt::layer())
        .init();

    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    init_tracing()?;

    let cfg = match envy::prefixed("").from_env::<Config>() {
        Ok(config) => config,
        Err(error) => {
            error!("configuration error: {}", error);
            std::process::exit(1);
        }
    };

    let client = redis::Client::open(cfg.redis_url).unwrap();
    let redis_connection = client.get_multiplexed_async_connection().await.unwrap();

    let queue_service = service::QueueService::new(redis_connection);

    let reflection_service = tonic_reflection::server::Builder::configure()
        .register_encoded_file_descriptor_set(proto::FILE_DESCRIPTOR_SET)
        .build_v1alpha()
        .unwrap();

    let addr = cfg.address.parse()?;
    info!("starting server on {}", cfg.address);

    Server::builder()
        .layer(TraceLayer::new_for_grpc())
        .add_service(service::queue::queue_server::QueueServer::new(
            queue_service,
        ))
        .add_service(reflection_service)
        .serve(addr)
        .await?;

    Ok(())
}
