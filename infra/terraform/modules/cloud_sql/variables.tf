# ── Cloud SQL module variables ─────────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # instance location
  description = "GCP region for the Cloud SQL instance"
  type        = string
}
