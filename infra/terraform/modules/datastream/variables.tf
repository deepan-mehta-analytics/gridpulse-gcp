# ── Datastream module variables ────────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # stream location
  description = "GCP region for the Datastream stream"
  type        = string
}
