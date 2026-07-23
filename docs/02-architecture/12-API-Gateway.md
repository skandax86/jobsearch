# API Gateway Architecture

**Document ID:** 02.12

**Version:** 1.0

**Status:** Draft

**Last Updated:** 2026-07-12

---

# 1. Purpose

The API Gateway is the single public entry point into the CareerPilot AI platform.

All client applications communicate through the API Gateway.

The gateway is responsible for request routing, authentication, authorization, rate limiting, API versioning, observability, and security.

Business logic does **not** belong in the API Gateway.

---

# 2. Goals

The API Gateway should:

- Provide a single API endpoint.
- Authenticate every request.
- Authorize every operation.
- Validate requests.
- Route traffic.
- Apply rate limiting.
- Support API versioning.
- Enable monitoring.
- Remain stateless.
- Support horizontal scaling.

---

# 3. High-Level Architecture

```text
                 Client Applications

        Web      Mobile      Browser Extension
                  │
                  ▼
          ┌────────────────────┐
          │     API Gateway     │
          └────────────────────┘
                  │
     ┌────────────┼─────────────┐
     ▼            ▼             ▼
 Candidate     Resume       Application
  Service      Service         Service
     │            │             │
     ▼            ▼             ▼
      AI Platform / ACP / MCP / Workers
```

---

# 4. Responsibilities

The API Gateway is responsible for:

- Authentication
- Authorization
- Request validation
- Routing
- Rate limiting
- API versioning
- Logging
- Metrics
- Request tracing
- Error normalization
- CORS
- Compression

---

# 5. Non-Responsibilities

The API Gateway must never:

- Execute AI agents
- Access databases directly
- Call MCP servers directly
- Execute business workflows
- Store business state

Business logic belongs to backend services.

---

# 6. Client Types

Supported clients include:

- Web Dashboard
- Browser Extension
- Mobile App (Future)
- Public REST API
- Internal Services

Every client communicates through HTTPS.

---

# 7. Request Lifecycle

```text
Client

↓

HTTPS Request

↓

Authentication

↓

Authorization

↓

Validation

↓

Routing

↓

Business Service

↓

Response

↓

Logging

↓

Client
```

---

# 8. Authentication

Supported methods:

- Email & Password
- Google OAuth
- GitHub OAuth
- Microsoft OAuth (Future)

Authentication returns:

- JWT Access Token
- Refresh Token

Tokens should have configurable expiration policies.

---

# 9. Authorization

Authorization is role-based.

Initial roles:

- Candidate
- Administrator
- Support

Future:

- Recruiter
- Organization Admin
- Enterprise User

Authorization is enforced before business logic executes.

---

# 10. API Versioning

API versions follow URL-based versioning.

Example:

```
/api/v1/users

/api/v1/jobs

/api/v1/applications
```

Breaking changes require a new API version.

---

# 11. Routing

Example routes:

```
/auth

/users

/resumes

/jobs

/companies

/applications

/interviews

/preferences

/workflows

/notifications

/analytics
```

Each route maps to a business service.

---

# 12. Validation

All requests are validated before reaching business services.

Validation includes:

- Schema validation
- Required fields
- Type validation
- Payload size
- File size
- Authentication
- Authorization

Invalid requests return standardized error responses.

---

# 13. Response Format

Every API returns a consistent envelope.

```json
{
  "success": true,
  "data": {},
  "metadata": {},
  "errors": [],
  "request_id": "uuid"
}
```

Error responses follow the same structure.

---

# 14. Rate Limiting

Rate limiting protects platform resources.

Examples:

Anonymous:

100 requests/hour

Authenticated:

1000 requests/hour

Premium:

Higher configurable limits

Limits are configurable and may vary by endpoint.

---

# 15. File Uploads

Supported uploads:

- PDF
- DOCX

Maximum size:

Configurable

Uploads should:

- Validate MIME type
- Validate size
- Scan for malware (future)
- Store in Object Storage

---

# 16. API Documentation

Every endpoint is documented using OpenAPI.

FastAPI automatically generates:

- Swagger UI
- OpenAPI Specification

Documentation must remain synchronized with implementation.

---

# 17. Error Handling

Standard HTTP status codes are used.

Examples:

200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

429 Too Many Requests

500 Internal Server Error

Responses should never expose internal implementation details.

---

# 18. Observability

Every request records:

- Request ID
- User ID
- Endpoint
- Method
- Status Code
- Latency
- IP Address (where appropriate)
- Correlation ID

Distributed tracing should propagate through downstream services.

---

# 19. Security

Security controls include:

- HTTPS only
- JWT validation
- OAuth
- Input validation
- Rate limiting
- CORS policy
- CSP headers (future)
- Audit logging

Secrets are managed outside the application.

---

# 20. Performance

Target objectives:

- Low request latency
- Stateless execution
- Efficient serialization
- Compression
- Connection pooling

The gateway should remain lightweight.

---

# 21. Scalability

The API Gateway supports:

- Horizontal scaling
- Load balancing
- Rolling deployments
- Blue/Green deployments
- Canary releases

Multiple gateway instances can run concurrently.

---

# 22. Future Enhancements

Future capabilities may include:

- GraphQL Gateway
- gRPC Gateway
- API Keys
- Webhooks
- WebSocket Gateway
- API Monetization
- Enterprise API Portal

---

# 23. Related Documents

- 02.03 Component Architecture
- 02.04 Service Architecture
- 02.08 Event-Driven Architecture
- 07 API
- 10 Security
- 11 Deployment