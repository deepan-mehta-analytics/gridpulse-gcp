# ── Root module — wires environment-scoped module instances ───────
provider "google" {        # configure the primary provider
  project = var.project_id # from variables.tf, no hardcoded ID
  region  = var.region
}

provider "google-beta" { # configure the beta provider identically
  project = var.project_id
  region  = var.region
}

module "budget" { # wired first, per spec §7.6 — cost guardrail before anything else
  source             = "./modules/budget"
  project_id         = var.project_id
  billing_account_id = var.billing_account_id
}

module "pubsub" { # messaging layer
  source     = "./modules/pubsub"
  project_id = var.project_id
}

module "gcs" { # raw landing + lifecycle tiering
  source     = "./modules/gcs"
  project_id = var.project_id
  region     = var.region
}

module "bigquery" { # bronze/silver/gold warehouse
  source     = "./modules/bigquery"
  project_id = var.project_id
  region     = var.region
}

module "biglake" { # lakehouse over GCS
  source     = "./modules/biglake"
  project_id = var.project_id
  region     = var.region
}

module "bigtable" { # wide-column, hot-lookup comparison (ADR 0002)
  source     = "./modules/bigtable"
  project_id = var.project_id
  region     = var.region
}

module "cloud_sql" { # OLTP for synthetic fleet/asset schema
  source     = "./modules/cloud_sql"
  project_id = var.project_id
  region     = var.region
}

module "cloud_run" { # ingestion collectors + FastAPI serving
  source     = "./modules/cloud_run"
  project_id = var.project_id
  region     = var.region
}

module "dataproc" { # batch backfill (Dataproc Serverless)
  source     = "./modules/dataproc"
  project_id = var.project_id
  region     = var.region
}

module "composer" { # orchestration (cloud demo windows only)
  source     = "./modules/composer"
  project_id = var.project_id
  region     = var.region
}

module "dataplex" { # catalog + DQ scans — cloud-only, no local twin
  source     = "./modules/dataplex"
  project_id = var.project_id
  region     = var.region
}

module "dlp" { # PII profiling, grounded in ADR 0003
  source     = "./modules/dlp"
  project_id = var.project_id
}

module "datastream" { # CDC — cloud-only, no local twin
  source     = "./modules/datastream"
  project_id = var.project_id
  region     = var.region
}

module "agent_engine" { # Tier 2/3 agent deployment (Phase 6+)
  source     = "./modules/agent_engine"
  project_id = var.project_id
  region     = var.region
}

module "monitoring" { # alert policies, cost dashboards
  source     = "./modules/monitoring"
  project_id = var.project_id
}
