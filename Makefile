# ── GridPulse Makefile ───────────────────────────────────────────
# Every target here is documented in the README "How to Run" section.

.PHONY: up down seed pipeline test-unit test-data test-contract test-integration test-agents cloud-up cloud-demo cloud-down lint fmt

up:                                        # start the full local emulator stack
	docker compose up -d                   # detached mode

down:                                      # stop and remove the local emulator stack
	docker compose down

seed:                                      # load seed/sample data into the local stack
	@echo "seed: not yet implemented — Phase 1 (ingest/collectors)"  # honest Phase 0 stub, not a silent no-op

pipeline:                                  # run the local end-to-end pipeline once
	@echo "pipeline: not yet implemented — Phase 1 (transform/beam)"

test-unit:                                 # run unit tests
	@echo "test-unit: no tests exist yet — Phase 0 scaffolding only"

test-data:                                 # run data-contract/schema validation tests
	@echo "test-data: no tests exist yet — Phase 0 scaffolding only"

test-contract:                             # run ingestion contract tests
	@echo "test-contract: no tests exist yet — Phase 0 scaffolding only"

test-integration:                          # run integration tests against the local stack
	@echo "test-integration: no tests exist yet — Phase 0 scaffolding only"

test-agents:                               # run the agent golden-question eval set
	@echo "test-agents: no tests exist yet — Phase 6 (agents/eval)"

cloud-up:                                  # provision the real-GCP demo window
	@if [ -z "$$GCP_BUDGET_ALERT_CONFIGURED" ]; then \
		echo "ERROR: cloud-up refuses to run without a configured budget alert."; \
		echo "Run: export GCP_BUDGET_ALERT_CONFIGURED=1 — only after confirming"; \
		echo "a real budget alert exists on the target project."; \
		exit 1; \
	fi
	@echo "cloud-up: Terraform apply not yet wired — Phase 7 (cloud demo window)"

cloud-demo:                                # run the scripted cloud demo walkthrough
	@echo "cloud-demo: not yet implemented — Phase 7"

cloud-down:                                # tear down the demo window, return spend to zero
	@echo "cloud-down: not yet implemented — Phase 7"

lint:                                      # lint Python, Terraform, and YAML
	@echo "lint: not yet wired — will run ruff + terraform fmt -check"

fmt:                                       # auto-format Python and Terraform
	@echo "fmt: not yet wired — will run ruff format + terraform fmt"
