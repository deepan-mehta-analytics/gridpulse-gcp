# ── Dataproc module variables ──────────────────────────────────
variable "project_id" { # target project
  description = "GCP project ID"
  type        = string
}

variable "region" { # batch job location
  description = "GCP region for Dataproc Serverless batch jobs"
  type        = string
}
