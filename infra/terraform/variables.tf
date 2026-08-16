# ── Root variables — parameterised by environment ─────────────────
variable "project_id" { # GCP project ID
  description = "GCP project ID — no default, must be supplied via terraform.tfvars (gitignored) or TF_VAR_project_id"
  type        = string # required, no placeholder default committed
}

variable "region" { # default GCP region
  description = "Default GCP region for all resources"
  type        = string
  default     = "europe-west2" # GB data — keeps demo latency honest, per repo CLAUDE.md
}

variable "environment" { # deployment environment name
  description = "Environment name: dev or prod"
  type        = string
  default     = "dev" # Phase 0 skeleton targets dev only
}

variable "billing_account_id" { # billing account, for the budget module only
  description = "Billing account ID — no default, must be supplied, never committed"
  type        = string
  sensitive   = true # marked sensitive so it never prints in plan/apply output
}
