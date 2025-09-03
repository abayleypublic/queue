variable "gcp_project_id" {
  description = "The ID of the GCP project in which the resources will be created."
  type        = string
  default     = "portfolio-463406"
}

variable "tenancy_ocid" {
  description = "Oracle Cloud tenancy OCID."
  type        = string
}

variable "user_ocid" {
  description = "Oracle Cloud user OCID."
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint of the Oracle Cloud user."
  type        = string
}

variable "private_key_path" {
  description = "Oracle Cloud private key."
  type        = string
}

variable "region" {
  description = "Oracle Cloud region."
  type        = string
  default     = "uk-london-1"
}

variable "compartment_id" {
  description = "Oracle Cloud compartment OCID."
  type        = string
  default     = "ocid1.compartment.oc1..aaaaaaaaeef3gmatoiwjkxw65hot2n3lb7qkxjuw5k3vebozv7wl2od7cwvq"
}

variable "key_id" {
  description = "OCID of the Oracle Cloud Vault key."
  type        = string
  default     = "ocid1.key.oc1.uk-london-1.eruckcfxaaarq.abwgiljtucsyrvx76zf5uwpb5flj5vyqgjqldzwdn25fwo2ssycgisrvvywq"
}

variable "vault_id" {
  description = "OCID of the Oracle Cloud Vault."
  type        = string
  default     = "ocid1.vault.oc1.uk-london-1.eruckcfxaaarq.abwgiljsf5ckladyqmxmnjo2zgc6sdymeqsic3ydbgrhuj7l2ulhl7k7mgda"
}
