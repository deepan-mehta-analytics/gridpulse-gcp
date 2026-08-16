# ── Composer module variables ──────────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # environment location
  description = "GCP region for the Composer environment"
  type        = string
}
