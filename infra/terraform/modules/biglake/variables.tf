# ── BigLake module variables ───────────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # catalog/connection location
  description = "GCP region for BigLake resources"
  type        = string
}
