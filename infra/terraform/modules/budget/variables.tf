# ── Budget module variables ────────────────────────────────────
variable "project_id" { # target project for the budget scope
  description = "GCP project ID this budget applies to"
  type        = string
}

variable "billing_account_id" { # billing account the budget is created under
  description = "Billing account ID — passed through from root, never hardcoded"
  type        = string
  sensitive   = true
}

variable "monthly_budget_gbp" { # spend ceiling
  description = "Monthly budget ceiling in GBP — kept low given the free-tier-first design"
  type        = number
  default     = 10 # deliberately small; cloud demo windows are short and capped
}
