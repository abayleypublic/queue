mod service;

use tonic::transport::Server;
use serde::Deserialize;
use tracing::{event, Level};

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

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cfg = match envy::prefixed("BACKEND_").from_env::<Config>() {
       Ok(config) => config,
       Err(error) => {
            event!(Level::ERROR, %error, "configuration error");
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
    event!(Level::INFO, "starting server on {}", cfg.address);

    Server::builder()
        .add_service(service::queue::queue_server::QueueServer::new(queue_service))
        .add_service(reflection_service)
        .serve(addr)
        .await?;

    Ok(())
}