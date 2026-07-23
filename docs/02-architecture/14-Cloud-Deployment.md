# Cloud Deployment Architecture

**Document ID:** 02.14

**Version:** 1.0

**Status:** Draft

**Last Updated:** 2026-07-12

---

# 1. Purpose

This document defines the cloud deployment architecture for CareerPilot AI.

The platform is designed as a cloud-native SaaS application capable of serving thousands of concurrent users while remaining secure, scalable, observable, and cost-efficient.

The deployment architecture is cloud-provider agnostic, with Google Cloud Platform (GCP) as the primary deployment target.

---

# 2. Goals

The deployment architecture should:

- Support SaaS deployment.
- Be cloud-native.
- Support zero-downtime deployments.
- Scale horizontally.
- Be highly available.
- Be secure.
- Support Infrastructure as Code.
- Enable disaster recovery.
- Support multiple environments.

---

# 3. Cloud Design Principles

The platform follows these principles:

- Everything is containerized.
- Infrastructure is declarative.
- Services are stateless.
- Storage is managed.
- Secrets are externalized.
- CI/CD is fully automated.
- Every component is replaceable.

---

# 4. Target Cloud Providers

Primary:

- Google Cloud Platform (GCP)

Supported Future:

- Amazon Web Services (AWS)
- Microsoft Azure
- Self-hosted Kubernetes

No application code should depend directly on a specific cloud provider.

---

# 5. High-Level Deployment

```text
                 Internet
                      │
                      ▼
             Cloud Load Balancer
                      │
                      ▼
                 API Gateway
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   Web Service    API Service   AI Orchestrator
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                 Worker Pool
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
 Browser Workers AI Workers Resume Workers
                      │
                      ▼
      PostgreSQL / Redis / GCS / pgvector
```

---

# 6. Deployment Environments

The platform supports:

Development

↓

Testing

↓

Staging

↓

Production

Each environment has isolated infrastructure.

---

# 7. Infrastructure Components

Core infrastructure includes:

- Load Balancer
- Kubernetes Cluster
- PostgreSQL
- Redis
- Object Storage
- Secret Manager
- Monitoring Stack
- CI/CD Pipeline

---

# 8. Kubernetes Deployment

Each runtime component is deployed independently.

Deployments include:

- Web
- API
- AI Orchestrator
- Workers
- Browser Workers
- MCP Services
- Monitoring

Every deployment supports rolling updates.

---

# 9. Container Strategy

Every deployable unit is packaged as a Docker image.

Images should be:

- Immutable
- Versioned
- Minimal
- Scanned for vulnerabilities

---

# 10. Scaling Strategy

Horizontal scaling is the default strategy.

Examples:

Increase:

- API replicas
- Worker replicas
- Browser workers
- AI workers

Scaling decisions are driven by metrics.

---

# 11. Load Balancing

External traffic:

Cloud Load Balancer

Internal traffic:

Kubernetes Services

Session affinity should be avoided unless required.

---

# 12. Service Discovery

Services communicate through internal DNS.

Example:

```
api-service

resume-worker

browser-worker

redis

postgres
```

Service addresses must never be hardcoded.

---

# 13. Networking

The deployment should use:

- Private networking
- Internal service communication
- HTTPS
- TLS
- Network Policies

Only public entry points are exposed to the internet.

---

# 14. Storage Deployment

Managed services are preferred.

Examples:

PostgreSQL

Cloud SQL

Redis

Managed Redis

Object Storage

Google Cloud Storage

Managed services reduce operational overhead.

---

# 15. Secret Management

Secrets are stored in:

Google Secret Manager

Future:

AWS Secrets Manager

Secrets include:

- API Keys
- OAuth Credentials
- Database Passwords
- JWT Keys

Secrets are injected at runtime.

---

# 16. Configuration Management

Configuration is externalized.

Examples:

- Environment Variables
- ConfigMaps
- Secrets
- Feature Flags

No environment-specific configuration is committed to source code.

---

# 17. CI/CD Pipeline

Deployment pipeline:

```text
Developer

↓

GitHub

↓

GitHub Actions

↓

Build

↓

Test

↓

Security Scan

↓

Docker Build

↓

Container Registry

↓

Deploy

↓

Health Check

↓

Production
```

---

# 18. Health Checks

Every service exposes:

- Liveness Probe
- Readiness Probe
- Startup Probe

Failed services are automatically restarted.

---

# 19. Observability

Every deployment exports:

- Metrics
- Logs
- Traces
- Health Status

Observability is mandatory for production.

---

# 20. Backup Strategy

Backup:

- PostgreSQL
- Object Storage Metadata
- Configuration

Backups are automated.

Recovery procedures are tested regularly.

---

# 21. Disaster Recovery

Deployment architecture supports:

- Zone failure
- Service failure
- Database recovery
- Object storage recovery

Future:

Multi-region deployment.

---

# 22. Security

Cloud deployment includes:

- IAM
- Private Networking
- Secret Manager
- Firewall Rules
- TLS
- WAF
- Kubernetes RBAC

Infrastructure follows least-privilege principles.

---

# 23. Cost Optimization

Strategies include:

- Autoscaling
- Scale-to-zero (where appropriate)
- Spot/Preemptible workers for non-critical tasks
- Lifecycle policies for storage
- Resource quotas
- Right-sized instances

Cost metrics are monitored continuously.

---

# 24. Multi-Tenancy

Future SaaS deployment supports:

- Shared infrastructure
- Tenant isolation
- Per-tenant quotas
- Per-tenant feature flags
- Tenant-specific analytics

---

# 25. Deployment Roadmap

### Phase 1

Docker Compose

↓

Single VM

### Phase 2

Cloud Run

↓

Managed PostgreSQL

### Phase 3

Kubernetes

↓

Autoscaling

↓

Public SaaS

### Phase 4

Multi-region Kubernetes

↓

Enterprise deployment

---

# 26. Future Enhancements

Future deployment capabilities:

- Blue/Green deployments
- Canary deployments
- GitOps
- Multi-region clusters
- Service Mesh
- Edge deployments

---

# 27. Related Documents

- 02.11 Worker Architecture
- 02.12 API Gateway
- 02.13 Security Architecture
- 11 Deployment
- 13 Observability