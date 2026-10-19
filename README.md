# Quizly Backend

Quizly Backend is an AI-powered Django REST Framework service that automatically converts YouTube videos into interactive 10-question multiple-choice quizzes.

Given a YouTube URL, the backend downloads the audio stream via `yt-dlp`, converts it with `FFmpeg`, transcribes the spoken speech locally using `OpenAI Whisper` (`base` model), and structures a validated ten-question quiz with four options and one correct answer using `Google Gemini 2.5 Flash`.

---

## Quickstart for Local Setup & Evaluation

This guide enables teachers, evaluators, and developers to clone, run, and test all functions of the backend immediately.

### 1. Prerequisites

- **Python 3.12+** (or Python 3.14)
- **Git**
- **FFmpeg** installed and accessible in the system's `PATH`:
  - **Windows (winget):**
    ```powershell
    winget install --id Gyan.FFmpeg -e --source winget
    ```
  - **macOS (Homebrew):**
    ```bash
    brew install ffmpeg
    ```
  - **Linux (Ubuntu/Debian):**
    ```bash
    sudo apt update && sudo apt install -y ffmpeg
    ```
  - *Verify:* `ffmpeg -version`
- **Google Gemini API Key**: Get a free API key from [Google AI Studio](https://aistudio.google.com/).

---

### 2. Installation & Server Start

```bash
# 1. Clone repository
git clone https://github.com/marioramirez90/quizly_backend.git
cd quizly_backend

# 2. Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Windows PowerShell:
Copy-Item .env.example .env
# macOS / Linux:
cp .env.example .env

# Open .env and add your SECRET_KEY and GEMINI_API_KEY:
# SECRET_KEY=your-django-secret-key-here
# DEBUG=True
# ALLOWED_HOSTS=localhost,127.0.0.1
# GEMINI_API_KEY=your-gemini-api-key-here

# 5. Run database migrations
python manage.py migrate

# 6. Create superuser for Django Admin (optional)
python manage.py createsuperuser

# 7. Start local development server
python manage.py runserver
```

- **API Base URL**: `http://127.0.0.1:8000/api/`
- **Django Admin**: `http://127.0.0.1:8000/admin/`

---

### 3. Quick Testing Guide for Examiners (Dozenten-Prüfungsanleitung)

You can verify all technical requirements (Definition of Done) and test all API features directly:

#### A. Automated Quality & DoD Checks

1. **Django System Check:**
   ```bash
   python manage.py check
   ```
   *(Result: 0 issues)*

2. **Run Test Suite:**
   ```bash
   python manage.py test
   ```
   *(Result: 55 of 55 tests passed)*

3. **Check Test Coverage:**
   ```bash
   coverage run --source='auth_app,quiz_app' manage.py test
   coverage report
   ```
   *(Result: 99% coverage, strictly exceeding the $\ge 95\%$ requirement)*

4. **Run PEP-8 Linter:**
   ```bash
   flake8 --exclude=.venv,migrations .
   ```
   *(Result: 0 errors, 0 warnings. All functions strictly $\le 14$ lines)*

---

#### B. Manual API Endpoint Walkthrough (cURL / REST Client)

With the server running on `http://127.0.0.1:8000/`, you can test all endpoints in order:

##### 1. Register User
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "teacher_test",
    "email": "teacher@example.com",
    "password": "SecurePassword123!",
    "confirmed_password": "SecurePassword123!"
  }'
```
*Expected: `201 Created` with `{"detail": "User created successfully!"}`*

##### 2. Login (sets HttpOnly cookies)
```bash
curl -X POST http://127.0.0.1:8000/api/login/ \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "teacher_test",
    "password": "SecurePassword123!"
  }'
```
*Expected: `200 OK`, sets `access_token` and `refresh_token` in cookies.*

##### 3. Generate a Quiz from YouTube
```bash
curl -X POST http://127.0.0.1:8000/api/quizzes/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'
```
*Expected: `201 Created` with 10 generated questions, options, and answer.*

##### 4. List Quizzes
```bash
curl -X GET http://127.0.0.1:8000/api/quizzes/ -b cookies.txt
# Optional filter:
curl -X GET "http://127.0.0.1:8000/api/quizzes/?period=today" -b cookies.txt
```
*Expected: `200 OK` with list of user's quizzes.*

##### 5. Get Quiz Details
```bash
curl -X GET http://127.0.0.1:8000/api/quizzes/1/ -b cookies.txt
```
*Expected: `200 OK` with quiz object, timestamps, video URL, and questions.*

##### 6. Update Quiz (Partial Update)
```bash
curl -X PATCH http://127.0.0.1:8000/api/quizzes/1/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Quiz Title", "description": "Updated Description"}'
```
*Expected: `200 OK` with updated title/description.*

##### 7. Delete Quiz
```bash
curl -X DELETE http://127.0.0.1:8000/api/quizzes/1/ -b cookies.txt
```
*Expected: `204 No Content` (permanently deletes quiz and cascade-deletes its questions).*

##### 8. Refresh Access Token
```bash
curl -X POST http://127.0.0.1:8000/api/token/refresh/ -b cookies.txt
```
*Expected: `200 OK` with renewed `access_token` cookie.*

##### 9. Logout
```bash
curl -X POST http://127.0.0.1:8000/api/logout/ -b cookies.txt
```
*Expected: `200 OK` with `{"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."}` and clears cookies.*

##### 10. Django Admin
Visit `http://127.0.0.1:8000/admin/` with your superuser credentials.
Inspect `QuizAdmin` (includes `QuestionInline` to edit all 10 questions inside a quiz) and standalone `QuestionAdmin`.

---

## Features

- **Automated Quiz Generation**: Extracts audio via `yt-dlp`, converts to MP3 via `FFmpeg`, transcribes speech via `Whisper`, and creates 10 validated questions via `Gemini`.
- **JWT Cookie Authentication**: Stateless authentication via HttpOnly cookies (`access_token`, `refresh_token`) protecting against XSS attacks.
- **Server-Side Token Blacklisting**: Blacklists refresh tokens upon logout using `rest_framework_simplejwt.token_blacklist`.
- **Owner-Based Access Control**: Strict multi-user isolation; users can only access their own quizzes (`403 Forbidden` / `404 Not Found`).
- **Comprehensive Admin Panel**: Inline editing of all questions linked to a quiz and standalone question management.
- **Clean Architecture & 100% DoD Compliance**: All functions $\le 14$ lines, Single Responsibility Principle, 0 Flake8 errors, 99% test coverage.

---

## Tech Stack

| Component | Technology | Description |
|:---|:---|:---|
| **Language** | Python 3.12+ / 3.14 | Core language |
| **Framework** | Django 6.1 | Web application framework |
| **API** | Django REST Framework 3.18 | RESTful API toolkit |
| **Authentication** | SimpleJWT with Token Blacklist | JWT stored in HTTP-only cookies |
| **Database** | SQLite (local dev) | Relational database (PostgreSQL-compatible) |
| **AI Model** | Google Gemini 2.5 Flash (`google-genai`) | AI question and options generator |
| **Speech-to-Text** | OpenAI Whisper (`base` model) | Local speech transcription |
| **Audio Processing** | `yt-dlp` & FFmpeg | YouTube audio extraction and conversion |
| **Testing** | Django Test Runner & Coverage | 55 automated unit/integration tests (99% coverage) |
| **Linter** | Flake8 | Clean code validation ($\le 14$ lines per function) |

---

## Environment Variables & Keys (`settings.py`)

All sensitive keys are managed via `.env` and loaded securely in [core/settings.py](file:///c:/Users/mario/Desktop/quizly_backend/core/settings.py):

| Variable | Description | Default / Example |
|:---|:---|:---|
| `SECRET_KEY` | Django cryptographic signing key | `django-insecure-...` (override in `.env`) |
| `DEBUG` | Enable/disable debug mode | `True` for dev, `False` for production |
| `ALLOWED_HOSTS` | Allowed hostnames/IPs | `localhost,127.0.0.1` |
| `GEMINI_API_KEY` | Google Gemini API key for AI generation | Your Gemini key from Google AI Studio |
| `FRONTEND_URL` | Trusted frontend origin for CORS | `http://localhost:5173` |

In `settings.py`:
- `SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-key")`
- `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")`
- `SIMPLE_JWT` uses `'SIGNING_KEY': SECRET_KEY` for cryptographically signing authentication tokens.

---

## API Endpoints Overview

All routes are prefixed with `/api/`:

| Method | Endpoint | Description | Auth Required |
|:---|:---|:---|:---|
| `POST` | `/api/register/` | Register user (`username`, `email`, `password`, `confirmed_password`) | No |
| `POST` | `/api/login/` | Log in and receive HTTP-only authentication cookies | No |
| `POST` | `/api/token/refresh/` | Refresh the access token using the refresh cookie | No |
| `POST` | `/api/logout/` | Log out, blacklist the refresh token, and clear cookies | Yes |
| `GET` | `/api/quizzes/` | List quizzes belonging to authenticated user (`?period=today`, `?period=7days`) | Yes |
| `POST` | `/api/quizzes/` | Generate a new quiz from a YouTube video URL | Yes |
| `GET` | `/api/quizzes/<id>/` | Retrieve a specific quiz owned by the user | Yes |
| `PATCH` | `/api/quizzes/<id>/` | Partially update quiz metadata (`title`, `description`) | Yes |
| `DELETE` | `/api/quizzes/<id>/` | Delete a quiz and all associated questions | Yes |

---

## Code Conventions & Clean Code Standards

- **Maximum Function Length**: Every function and method is strictly **$\le 14$ lines long**.
- **Single Responsibility Principle**: Every function performs exactly one specific task.
- **Naming Conventions**: Strict `snake_case` for functions/variables and `PascalCase` for classes.
- **Clean Architecture**:
  - `views.py`: Request handling and response returning only.
  - `utils.py`: Reusable business logic, AI orchestration, and helper functions.
  - `serializers.py`: Data serialization, deserialization, and validation.
- **Documentation**: Comprehensive docstrings on all modules, classes, and methods.
- **Zero Orphaned Code**: No commented-out code blocks or orphan `print()` statements.
