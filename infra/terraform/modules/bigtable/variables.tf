# ── Bigtable module variables ──────────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # instance/cluster location
  description = "GCP region for the Bigtable instance"
  type        = string
}
