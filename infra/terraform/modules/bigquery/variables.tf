# ── BigQuery module variables ──────────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # dataset location
  description = "GCP region for dataset placement"
  type        = string
}
