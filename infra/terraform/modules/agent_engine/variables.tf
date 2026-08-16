# ── Agent Engine module variables ──────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # deployment location
  description = "GCP region for Agent Engine deployment"
  type        = string
}
