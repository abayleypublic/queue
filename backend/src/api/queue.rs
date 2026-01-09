pub mod queue {
    tonic::include_proto!("queue");
}

use queue::queue_server::Queue;
use queue::{Entity, GetQueueRequest, GetQueueResponse, SetQueueRequest, SetQueueResponse};
use redis::AsyncCommands;
use redis::aio::MultiplexedConnection;
use tonic::{Request, Response, Status};
use tracing::Instrument;
use tracing::{debug, info_span};

use crate::api::middleware::user_from_request;

#[derive(Debug, Clone)]
pub struct QueueService {
    // Plain redis multiplexed connection (cheap to clone & send cmds on).
    redis: MultiplexedConnection,
}

fn queue_key(queue: String) -> String {
    format!("queue:{queue}")
}

impl QueueService {
    pub fn new(redis: MultiplexedConnection) -> Self {
        Self { redis }
    }
}

#[tonic::async_trait]
impl Queue for QueueService {
    async fn get_queue(
        &self,
        request: Request<GetQueueRequest>,
    ) -> Result<Response<GetQueueResponse>, Status> {
        debug!("received get_queue request: {:?}", request);

        let user = user_from_request(&request);
        if user.is_none() || user.unwrap().email.is_empty() {
            return Err(Status::unauthenticated("user not authenticated"));
        }

        let key = queue_key(request.into_inner().id);

        let mut conn = self.redis.clone();

        let res: Vec<String> = conn
            .lrange(&key, 0, -1)
            .instrument(info_span!("redis", cmd = "LRANGE", key = %key))
            .await
            .map_err(|e| Status::internal(format!("Redis error: {e}")))?;

        let entities: Vec<Entity> = res
            .into_iter()
            .filter_map(|item| serde_json::from_str(&item).ok())
            .collect();

        Ok(Response::new(GetQueueResponse { entities }))
    }

    async fn set_queue(
        &self,
        request: Request<SetQueueRequest>,
    ) -> Result<Response<SetQueueResponse>, Status> {
        debug!("received set_queue request: {:?}", request);

        let user = user_from_request(&request);
        if user.is_none() || user.unwrap().email.is_empty() {
            return Err(Status::unauthenticated("user not authenticated"));
        }

        let inner = request.into_inner();
        let key = queue_key(inner.id);

        let mut conn = self.redis.clone();

        let _: i64 = conn
            .del(&key)
            .instrument(info_span!("redis", cmd = "DEL", key = %key))
            .await
            .map_err(|e| Status::internal(format!("Redis error on delete: {e}")))?;

        if inner.entities.is_empty() {
            return Ok(Response::new(SetQueueResponse {}));
        }

        let entities: Vec<String> = inner
            .entities
            .into_iter()
            .filter_map(|entity| serde_json::to_string(&entity).ok())
            .collect();

        let span = info_span!("redis", cmd = "RPUSH", key = %key, count = entities.len());
        let _: i64 = conn
            .rpush(&key, entities)
            .instrument(span)
            .await
            .map_err(|e| Status::internal(format!("Redis error on push: {e}")))?;

        Ok(Response::new(SetQueueResponse {}))
    }
}
