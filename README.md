# cmpe272-github-issues-service

# GitHub Issues Service

A FastAPI service that wraps the GitHub Issues REST API for the CMPE 272 project.

## Repository

Service repository:

`https://github.com/cmpe272-git-happens/cmpe272-github-issues-service`

The service uses the following test repository:

`https://github.com/cmpe272-git-happens/cmpe272-issues-test`

---

## Prerequisites

Install the following before starting:

* Python 3.10+
* Git
* A GitHub account with access to the project repositories

Check your Python version:

### macOS / Linux

```bash
python3 --version
git --version
```

### Windows PowerShell

```powershell
python --version
git --version
```

If `python` is not recognized on Windows, try:

```powershell
py --version
```

---

# Setup

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

---

## 2. Create a virtual environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activation, your terminal should show something similar to:

```text
(.venv) user@computer ...
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script with an execution-policy error, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

If using Command Prompt instead of PowerShell:

```cmd
py -m venv .venv
.venv\Scripts\activate.bat
```

---

## 3. Install dependencies

Make sure the virtual environment is activated.

### macOS / Linux / Windows

```bash
pip install -r requirements.txt
```

The project dependencies currently include:

* FastAPI
* Uvicorn
* HTTPX
* pytest
* pytest-cov
* python-dotenv

---

## 4. Configure environment variables

Create a local `.env` file in the project root.

Do **not** commit `.env` to GitHub.

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

Then open `.env` and fill in the required values:

```env
GITHUB_TOKEN=YOUR_GITHUB_TOKEN
GITHUB_OWNER=cmpe272-git-happens
GITHUB_REPO=cmpe272-issues-test
WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET
PORT=8000
```

### Important

Never commit or push:

```text
.env
```

The `.gitignore` file already excludes it.

Do not share your GitHub token or webhook secret in the GitHub repository, README, screenshots, or team chat.

---

# Run the Service

Make sure your virtual environment is activated.

### macOS / Linux / Windows

```bash
uvicorn app.main:app --reload --port 8000
```

The service should start at:

```text
http://localhost:8000
```

You should see output similar to:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

# Verify the Service

Open the following in your browser:

### Health check

```text
http://localhost:8000/healthz
```

Expected response:

```json
{
  "status": "ok"
}
```

### Swagger API documentation

```text
http://localhost:8000/docs
```

FastAPI automatically provides the interactive Swagger UI.

### OpenAPI specification

```text
http://localhost:8000/openapi.json
```

---

# Stop the Service

Press:

```text
Ctrl + C
```

If Uvicorn does not stop immediately when using `--reload`, press `Ctrl + C` again.

---

# Running Tests

Tests will be added as the project is developed.

Once tests are available:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

---

# Project Structure

```text
cmpe272-github-issues-service/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   └── routes/
│       ├── __init__.py
│       ├── issues.py
│       ├── webhook.py
│       ├── events.py
│       └── health.py
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# Development Workflow

Each team member should work on their own branch.

First make sure your local `main` branch is up to date:

```bash
git checkout main
git pull origin main
```

Create a feature branch:

```bash
git checkout -b feature/<your-feature-name>
```

Example:

```bash
git checkout -b feature/github-client
```

After making changes:

```bash
git add .
git commit -m "feat: describe your change"
git push -u origin feature/<your-feature-name>
```

Then open a Pull Request on GitHub.

## Important

Do not push directly to `main` for feature work.

Pull changes from `main` before starting new work so that everyone is working from the latest version.

---

# Team Repository

The GitHub Issues used for testing are stored in the separate test repository:

`https://github.com/cmpe272-git-happens/cmpe272-issues-test`

The service repository contains the application code.

The test repository is used as the controlled GitHub repository against which the service will perform issue operations.

---

# Current Status

Phase 0 setup is complete.

Current functionality:

* FastAPI application
* `/healthz` health endpoint
* `/issues` router
* `/webhook` router
* `/events` router
* Automatic Swagger documentation
* Environment-based configuration
* Python virtual environment support
* macOS/Linux and Windows setup
* Git-based team development workflow

Additional GitHub Issues functionality, webhooks, persistence, testing, Docker, CI/CD, and other assignment requirements will be implemented in subsequent phases.
