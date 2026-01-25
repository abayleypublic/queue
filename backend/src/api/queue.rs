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

        let user = user_from_request(&request)
            .ok_or_else(|| Status::unauthenticated("user not authenticated"))?;

        if user.email.is_empty() {
            return Err(Status::unauthenticated("user email is required"));
        }

        let inner = request.into_inner();

        // Validate that user only has at most one entity in the queue
        let user_entities: Vec<&Entity> = inner
            .entities
            .iter()
            .filter(|e| e.id == user.email)
            .collect();

        if user_entities.len() > 1 {
            return Err(Status::invalid_argument(
                "users can only have one entity in a queue",
            ));
        }

        // Get current queue state to validate changes
        let key = queue_key(inner.id.clone());
        let mut conn = self.redis.clone();

        let existing: Vec<String> = conn
            .lrange(&key, 0, -1)
            .instrument(info_span!("redis", cmd = "LRANGE", key = %key))
            .await
            .map_err(|e| Status::internal(format!("Redis error: {e}")))?;

        let existing_entities: Vec<Entity> = existing
            .into_iter()
            .filter_map(|item| serde_json::from_str(&item).ok())
            .collect();

        for entity in &inner.entities {
            if entity.id != user.email {
                let entity_existed = existing_entities
                    .iter()
                    .any(|e| e.id == entity.id && e.name == entity.name);

                if !entity_existed {
                    return Err(Status::permission_denied(format!(
                        "users can only add or modify entities with their email as the ID ({})",
                        user.email
                    )));
                }
            }
        }

        for existing_entity in &existing_entities {
            if existing_entity.id != user.email {
                let still_exists = inner.entities.iter().any(|e| e.id == existing_entity.id);

                if !still_exists {
                    return Err(Status::permission_denied(
                        "users cannot remove entities that don't belong to them",
                    ));
                }
            }
        }

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
