# ── Cloud Run module variables ─────────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # service location
  description = "GCP region for Cloud Run services"
  type        = string
}
