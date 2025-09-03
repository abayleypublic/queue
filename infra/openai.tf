# ==========
# Staging
# ==========

resource "oci_vault_secret" "stg_queue_openai_api_key" {
  compartment_id = var.compartment_id
  key_id         = var.key_id
  secret_name    = "stg_queue_openai_api_key"
  vault_id       = var.vault_id

  secret_content {
    content_type = "BASE64"
    content      = base64encode("UkVQTEFDRV9NRQ==")
  }
}

# ==========
# Production
# ==========

resource "oci_vault_secret" "prod_queue_openai_api_key" {
  compartment_id = var.compartment_id
  key_id         = var.key_id
  secret_name    = "prod_queue_openai_api_key"
  vault_id       = var.vault_id

  secret_content {
    content_type = "BASE64"
    content      = base64encode("UkVQTEFDRV9NRQ==")
  }
}
