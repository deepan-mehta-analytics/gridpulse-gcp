# ── Dataplex module variables ──────────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # lake/zone location
  description = "GCP region for Dataplex resources"
  type        = string
}
