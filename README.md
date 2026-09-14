# CMPE 272 – GitHub Issues Service

A FastAPI service that wraps the GitHub Issues REST API for the CMPE 272 project.

## Repositories

**Service repository:**  
https://github.com/cmpe272-git-happens/cmpe272-github-issues-service

**Controlled test repository:**  
https://github.com/cmpe272-git-happens/cmpe272-issues-test

The service repository contains the application code. The separate test repository is the controlled GitHub repository against which issue and comment operations are performed.

## Prerequisites

Install:

- Python 3.14+
- Git
- Docker (optional, for containerized execution)
- A GitHub account with access to the project repositories
- A GitHub fine-grained personal access token with the required repository permissions

Check versions:

### macOS / Linux
```bash
python3 --version
git --version
docker --version
```

### Windows PowerShell
```powershell
python --version
git --version
docker --version
```

# Run the Service Locally

## 1. Clone the repository

### macOS / Linux
```bash
cd ~/Desktop
git clone https://github.com/cmpe272-git-happens/cmpe272-github-issues-service.git
cd cmpe272-github-issues-service
```

### Windows PowerShell
```powershell
cd $HOME\Desktop
git clone https://github.com/cmpe272-git-happens/cmpe272-github-issues-service.git
cd cmpe272-github-issues-service
```

## 2. Create and activate a virtual environment

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Windows Command Prompt
```cmd
py -m venv .venv
.venv\Scripts\activate.bat
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project uses FastAPI, Uvicorn, HTTPX, pytest, pytest-cov, and python-dotenv.

## 4. Configure environment variables

Copy `.env.example` to `.env`.

### macOS / Linux
```bash
cp .env.example .env
```

### Windows PowerShell
```powershell
Copy-Item .env.example .env
```

### Windows Command Prompt
```cmd
copy .env.example .env
```

Edit `.env`:
```env
GITHUB_TOKEN=YOUR_GITHUB_TOKEN
GITHUB_OWNER=cmpe272-git-happens
GITHUB_REPO=cmpe272-issues-test
WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET
PORT=8000
```

Never commit `.env` or expose the real GitHub token/webhook secret in source code, screenshots, README files, or chat.

## 5. Start the service

```bash
uvicorn app.main:app --reload --port 8000
```

The service runs at:
```text
http://localhost:8000
```

## 6. Verify the service

Health check:
```text
http://localhost:8000/healthz
```

Expected response:
```json
{"status": "ok"}
```

Interactive API documentation:
```text
http://localhost:8000/docs
```

OpenAPI document:
```text
http://localhost:8000/openapi.json
```

## 7. Stop the service

Press `Ctrl + C`.

# Run Tests

From the project root with the virtual environment activated:

```bash
pytest
```

Run the full suite with coverage:

```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

The integrated regression suite currently contains 73 tests and has achieved 93.50% total coverage.

# Run with Docker

Build the image:
```bash
docker build -t cmpe272-github-issues-service .
```

Run the container:
```bash
docker run --rm -p 8000:8000 --env-file .env cmpe272-github-issues-service
```

Verify:
```text
http://localhost:8000/healthz
```

Swagger:
```text
http://localhost:8000/docs
```

To see the running container:
```bash
docker ps
```

# CI/CD

GitHub Actions runs the automated test suite on pushes and pull requests.

The CI test job requires at least 50% coverage.

When changes are pushed to the `dev` branch and tests pass, the pipeline builds and publishes the Docker image to GitHub Container Registry (GHCR).

The workflow is located at:
```text
.github/workflows/ci.yml
```

# Project Structure

```text
cmpe272-github-issues-service/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── github_client.py
│   ├── logging_config.py
│   ├── main.py
│   ├── middleware.py
│   ├── schemas.py
│   └── routes/
│       ├── __init__.py
│       ├── events.py
│       ├── health.py
│       ├── issues.py
│       └── webhook.py
├── tests/
├── .github/
│   └── workflows/
│       └── ci.yml
├── Dockerfile
├── .dockerignore
├── .env.example
├── .gitignore
├── openapi.yaml
├── pytest.ini
├── requirements.txt
└── README.md
```

# Development Workflow

Each team member works on a separate branch and changes are merged through pull requests.

Before starting work:
```bash
git switch dev
git pull origin dev
```

Create a feature branch:
```bash
git switch -c feature/<your-feature-name>
```

After making changes:
```bash
git add .
git commit -m "feat: describe your change"
git push -u origin feature/<your-feature-name>
```

Open a pull request into `dev`.

Do not push feature work directly to `dev`.

# Current Implementation

The service currently provides:

- FastAPI REST API
- GitHub Issues CRUD operations
- Issue comments
- DELETE-as-close behavior
- Pagination and GitHub Link header handling
- GitHub API rate-limit/error handling
- GitHub webhooks for `issues`, `issue_comment`, and `ping`
- HMAC SHA-256 webhook signature validation
- Webhook delivery idempotency/persistence using SQLite
- ETag / conditional GET support
- Request IDs
- Structured request logging with status and latency
- `/healthz`
- OpenAPI documentation
- Automated unit/integration tests
- Docker containerization
- GitHub Actions CI
- Docker CI/CD publishing to GHCR
