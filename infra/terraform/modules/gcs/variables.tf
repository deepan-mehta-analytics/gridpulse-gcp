# ── GCS module variables ───────────────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # bucket location
  description = "GCP region for bucket placement"
  type        = string
}
