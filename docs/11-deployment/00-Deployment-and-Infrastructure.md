# Deployment and Infrastructure

**Document ID:** 11.00  
**Status:** Draft

## Purpose

Defines how CareerPilot is built, provisioned, released, and operated across development, staging, and production.

## Environments

Development uses Docker Compose and local emulators where useful. Staging mirrors production identity, networking, and deployment controls with isolated data. Production uses managed GCP services initially: Cloud Run where suitable, Cloud SQL for PostgreSQL/pgvector, managed Redis, GCS, Secret Manager, Cloud Load Balancing/WAF, and a container registry. GKE is introduced for workload patterns requiring stronger worker/browser control.

## Infrastructure Rules

- Terraform is the source of truth for cloud resources, IAM, networking, storage, and managed services.
- Deploy immutable, scanned Docker images by digest.
- Keep APIs and workers stateless; configuration and secrets are injected at runtime.
- Use private service networking, least-privilege service accounts, and separate cloud projects/accounts per environment.
- Run browser workers in isolated, resource-limited containers; never persist credentials in images.

## Release Pipeline

`lint → unit tests → contract/integration tests → security scans → image build → staging deploy → smoke tests → approval/promotion → production deploy → health verification`.

Use rolling deployment initially; add canary/blue-green only when release risk or traffic justifies it. Every deployment has an observable version, rollback target, and migration compatibility plan.

## Related Documents

- [14-Cloud-Deployment.md](../02-architecture/14-Cloud-Deployment.md)
- [15-Scalability.md](../02-architecture/15-Scalability.md)
- [00-Testing-Strategy.md](../12-testing/00-Testing-Strategy.md)
