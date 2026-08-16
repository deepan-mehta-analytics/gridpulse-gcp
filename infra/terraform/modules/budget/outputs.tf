# ── Budget module outputs ──────────────────────────────────────
output "budget_name" { # confirms the budget resource name for cloud-up's guard check
  description = "Resource name of the created budget alert"
  value       = google_billing_budget.gridpulse.name
}
