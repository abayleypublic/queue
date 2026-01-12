use crate::user::user::User;
use tonic::{Request, Status};

pub fn auth_interceptor(mut req: Request<()>) -> Result<Request<()>, Status> {
    let email = req
        .metadata()
        .get("x-auth-request-email")
        .and_then(|v| v.to_str().ok());

    let user = User {
        email: email.unwrap_or("").to_string(),
    };

    req.extensions_mut().insert(user);
    Ok(req)
}

pub fn user_from_request<T>(req: &Request<T>) -> Option<User> {
    req.extensions().get::<User>().cloned()
}
