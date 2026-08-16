# ── Root outputs — surfaced for use by CI and documentation ───────
output "project_id" { # echo back the target project for confirmation in plan output
  description = "GCP project this configuration targets"
  value       = var.project_id
}

output "region" { # echo back the default region
  description = "Default GCP region"
  value       = var.region
}
