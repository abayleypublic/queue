pub mod queue {
    tonic::include_proto!("queue");
}

use log::debug;
use queue::queue_server::Queue;
use queue::{Entity, GetQueueRequest, GetQueueResponse, SetQueueRequest, SetQueueResponse};
use redis::AsyncCommands;
use redis::aio::MultiplexedConnection;
use tonic::{Request, Response, Status};

#[derive(Debug, Clone)]
pub struct QueueService {
    redis: MultiplexedConnection,
}

fn queue_key(queue: String) -> String {
    format!("queue:{}", queue)
}

impl QueueService {
    pub fn new(redis: MultiplexedConnection) -> Self {
        QueueService { redis }
    }
}

#[tonic::async_trait]
impl Queue for QueueService {
    async fn get_queue(
        &self,
        request: Request<GetQueueRequest>,
    ) -> Result<Response<GetQueueResponse>, Status> {
        debug!("received get_queue request: {:?}", request);

        let key = queue_key(request.into_inner().id);
        let res: Vec<String> = self
            .redis
            .clone()
            .lrange(key, 0, -1)
            .await
            .map_err(|e| Status::internal(format!("Redis error: {}", e)))?;

        let entities: Vec<Entity> = res
            .into_iter()
            .filter_map(|item| serde_json::from_str(&item).ok())
            .collect();

        let response = GetQueueResponse { entities: entities };

        Ok(Response::new(response))
    }

    async fn set_queue(
        &self,
        request: Request<SetQueueRequest>,
    ) -> Result<Response<SetQueueResponse>, Status> {
        debug!("received set_queue request: {:?}", request);

        let inner = request.into_inner();
        let key = queue_key(inner.id);
        let _: () = self
            .redis
            .clone()
            .del::<_, ()>(&key)
            .await
            .map_err(|e| Status::internal(format!("Redis error on delete: {}", e)))?;

        // Push the new entities to the Redis list
        let entities: Vec<String> = inner
            .entities
            .into_iter()
            .filter_map(|entity| serde_json::to_string(&entity).ok())
            .collect();

        if entities.is_empty() {
            let _: () = self
                .redis
                .clone()
                .del(&key)
                .await
                .map_err(|e| Status::internal(format!("Redis error on push: {}", e)))?;

            return Ok(Response::new(SetQueueResponse {}));
        }

        let _: () = self
            .redis
            .clone()
            .rpush(&key, entities)
            .await
            .map_err(|e| Status::internal(format!("Redis error on push: {}", e)))?;

        Ok(Response::new(SetQueueResponse {}))
    }
}
