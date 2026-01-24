terraform {
  backend "gcs" {
    bucket = "b255f83f593efd7a-infra-terraform-state"
    prefix = "queue"
  }
}
