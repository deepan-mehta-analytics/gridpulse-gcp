# ── Provider and Terraform version constraints ───────────────────
terraform {
  required_version = ">= 1.6.0" # Phase 0 bar: validate/plan only, no apply

  required_providers {
    google = { # primary GCP provider
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = { # needed for preview features (Conversational Analytics, Agent Engine)
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}
