terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 7.0.0"
    }
  }
}

provider "google" {
  project               = var.gcp_project_id
  billing_project       = var.gcp_project_id
  user_project_override = true
  region                = "europe-west1"
}

provider "oci" {
  region           = var.region
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
}
