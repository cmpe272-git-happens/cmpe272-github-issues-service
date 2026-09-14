# CMPE 272 – HW #2
# GitHub Issues Service – Design Note

## 1. Purpose

The GitHub Issues Service is a FastAPI-based service that wraps the
GitHub Issues REST API. The service provides a clean HTTP interface for
issue and comment operations on a controlled GitHub repository.

The service also receives GitHub webhook events, validates webhook
signatures, persists event information locally, and prevents duplicate
webhook deliveries from being processed multiple times.

## 2. Architecture

The service consists of the following major components:

- FastAPI routes for issues, webhooks, events, and health checks
- A GitHub client using HTTPX for outbound GitHub REST API calls
- SQLite persistence for webhook/event state and idempotency
- Pydantic schemas for request validation
- Middleware for request IDs and structured logging
- Docker for containerization
- GitHub Actions for CI/CD

The main request flow is:

Client → FastAPI → GitHub Client → GitHub REST API

GitHub Webhooks → `/webhook` → HMAC Validation → Event Processing → SQLite

## 3. REST API and GitHub Integration

The service provides HTTP endpoints for:

- Listing issues
- Creating issues
- Retrieving an issue
- Updating an issue
- Closing an issue
- Listing issue comments
- Creating issue comments

The service treats `DELETE /issues/{issue_number}` as a request to close
the issue rather than permanently delete it.

GitHub pagination information is handled through Link headers, allowing
clients to follow additional pages of results. GitHub API errors and
rate-limit responses are handled by the GitHub client layer.

## 4. Request Validation

Pydantic models validate incoming requests.

Issue creation requires a non-empty title. Issue updates support
optional title and body fields and restrict issue state to `open` or
`closed`. Comment creation requires a non-empty comment body.

Invalid request payloads return HTTP 400 responses with structured
validation information.

## 5. Webhooks, Security, and Idempotency

The webhook endpoint supports:

- `issues`
- `issue_comment`
- `ping`

Webhook requests are validated using HMAC SHA-256 and the configured
webhook secret. The signature is verified against the raw request body
before event processing.

Webhook delivery IDs are persisted locally to support idempotent event
processing. Duplicate deliveries can therefore be recognized and
acknowledged without processing the same event multiple times.

Secrets are supplied through environment variables rather than stored
in source code.

## 6. Persistence

SQLite is used for local persistence of webhook/event information
needed for delivery tracking and duplicate detection.

SQLite was selected because it satisfies the local persistence
requirement without requiring a separate database server and is
appropriate for the scope of this project.

## 7. ETag / Conditional GET

The service supports ETag-based conditional requests.

For supported GET operations, the service generates an ETag representing
the current response. A client can subsequently send an
`If-None-Match` header. If the resource has not changed, the service can
return `304 Not Modified`, avoiding unnecessary transfer of unchanged
response data.

## 8. Observability

The service implements request ID and structured logging middleware.

Each request receives an `X-Request-ID`. If the client provides an
existing request ID, the service preserves it.

The middleware records:

- Service name
- Request ID
- HTTP method
- Endpoint
- HTTP status
- Request latency

The request ID is also returned in the response headers.

## 9. Health Check

The service exposes:

`GET /healthz`

A successful response is:

```json
{
  "status": "ok"
}
```

The endpoint provides a lightweight way to determine whether the
application is running.

## 10. Testing and Quality

The project includes automated tests using pytest and pytest-cov.

The test suite covers:

- Database functionality
- ETag behavior
- GitHub client functionality
- Health checks
- Issue routes
- OpenAPI behavior
- Request validation
- Webhook validation and processing

The final integrated regression run contained 73 passing tests with
93.50% total code coverage, exceeding the assignment's 80% coverage
target.

## 11. Containerization and CI/CD

The application is packaged using a Python 3.14 slim Docker image and
served with Uvicorn.

GitHub Actions runs the automated test suite on pushes and pull
requests with a coverage gate. For pushes to the `dev` branch, the
successful test job is a prerequisite for building and publishing the
Docker image to GitHub Container Registry (GHCR).

This ensures that a Docker image is not published when the automated
tests fail.

## 12. Design Tradeoffs

### FastAPI

FastAPI provides lightweight HTTP routing, automatic OpenAPI
documentation, and Pydantic-based request validation.

### HTTPX

HTTPX provides the HTTP client used to communicate with the GitHub REST
API.

### SQLite

SQLite provides local persistence without requiring an additional
database service. This keeps the project simple while satisfying the
assignment requirements.

### Docker

Docker provides a reproducible runtime environment and allows the
service to be executed consistently across development environments.

### GitHub Actions

GitHub Actions integrates automated testing and Docker image publishing
with the team's GitHub workflow.

## 13. Security Considerations

Sensitive credentials are supplied through environment variables.

The following values are not stored in source code:

- GitHub personal access token
- GitHub webhook secret

The local `.env` file is excluded from version control and the Docker
build context using `.gitignore` and `.dockerignore`.

The GitHub token uses the minimum repository permissions required by the
service.

Webhook signatures are verified using HMAC SHA-256 before event
processing.

## 14. Team Contributions

### Thanzeel Hassan

- Application integration
- Environment configuration
- Request ID middleware
- Structured logging
- Health check
- Docker configuration
- GitHub Actions CI
- CI/CD and Docker image publishing
- Final integration and regression testing

### Navaneeth Puklath

- GitHub API client
- Issue CRUD operations
- Issue comments
- Pagination
- GitHub API error and rate-limit handling

### Sukruti Shah

- GitHub webhook processing
- HMAC SHA-256 signature validation
- Webhook event persistence
- Webhook idempotency
- Webhook tests

### Juilee Giramkar

- OpenAPI specification
- Automated test development
- API/test coverage

## 15. Conclusion

The final service provides a FastAPI-based interface over GitHub Issues
with issue and comment operations, webhook processing, HMAC validation,
local persistence, idempotency, ETag support, structured logging,
automated testing, Docker containerization, and GitHub Actions CI/CD.

The integrated test suite passes all 73 tests with 93.50% code coverage,
and the CI/CD pipeline successfully builds and publishes the Docker image
after successful tests on the `dev` branch.
