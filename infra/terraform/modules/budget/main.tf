# ── Budget alert — the guardrail cloud-up checks for ──────────────
resource "google_billing_budget" "gridpulse" { # the actual budget resource
  billing_account = var.billing_account_id     # never a real ID committed — passed via TF_VAR
  display_name    = "gridpulse-monthly-budget" # identifiable in the GCP console

  budget_filter { # scope the budget to this project only
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount { # fixed GBP ceiling, not percentage-of-last-period
      # Must match the target billing account's own currency or `apply` fails
      # with a non-obvious error — verify the real billing account's currency
      # before this is ever applied (Phase 7), don't assume GBP.
      currency_code = "GBP"
      units         = tostring(var.monthly_budget_gbp)
    }
  }

  threshold_rules { # alert at 50% of budget
    threshold_percent = 0.5
  }
  threshold_rules { # alert at 90% of budget
    threshold_percent = 0.9
  }
  threshold_rules { # alert at 100% of budget
    threshold_percent = 1.0
  }
}
