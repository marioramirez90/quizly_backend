# Quizly Backend

Quizly Backend is an AI-powered Django REST Framework service that automatically turns YouTube videos into interactive multiple-choice quizzes. 

Given a YouTube link, the backend downloads the audio track, converts it using FFmpeg, transcribes the speech locally using OpenAI Whisper, and uses Google Gemini to generate a validated 10-question multiple-choice quiz stored securely in the database.

---

## Quickstart

Follow these steps to get Quizly Backend running locally in just a few minutes.

### 1. Prerequisites

Make sure the following software is installed on your system:

- **Python 3.12+** (or Python 3.14)
- **Git**
- **FFmpeg** installed globally and accessible in your system `PATH`.
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
  - Verify installation:
    ```bash
    ffmpeg -version
    ```
- A **Google Gemini API Key** from [Google AI Studio](https://aistudio.google.com/).

---

### 2. Setup & Installation

#### Clone the repository
```bash
git clone https://github.com/marioramirez90/quizly_backend.git
cd quizly_backend
```

#### Create & activate a virtual environment
```bash
python -m venv .venv
```

| Operating System | Activation Command |
|:---|:---|
| **Windows PowerShell** | `.\.venv\Scripts\Activate.ps1` |
| **Windows Command Prompt** | `.venv\Scripts\activate.bat` |
| **macOS / Linux** | `source .venv/bin/activate` |

#### Install dependencies
```bash
pip install -r requirements.txt
```

#### Configure environment variables
Copy the example configuration to create your local `.env`:

- **Windows PowerShell:**
  ```powershell
  Copy-Item .env.example .env
  ```
- **macOS / Linux:**
  ```bash
  cp .env.example .env
  ```

Open `.env` and configure your credentials:
```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
GEMINI_API_KEY=your-gemini-api-key-here
```

#### Run database migrations
```bash
python manage.py migrate
```

#### Create an administrator account (optional)
```bash
python manage.py createsuperuser
```

#### Start the development server
```bash
python manage.py runserver
```

The service is now running:
- **API Root**: `http://127.0.0.1:8000/api/`
- **Django Admin**: `http://127.0.0.1:8000/admin/`

---

## Features

- **Automated Quiz Generation**: Converts any supported YouTube video URL into a 10-question multiple-choice quiz.
- **Local Speech-to-Text**: Offline transcription via OpenAI's Whisper `base` model without requiring external transcription APIs.
- **Generative AI with Gemini**: Formulates structured questions, 4 distinct options, and 1 verified correct answer using Google Gemini 2.5 Flash.
- **Secure Cookie-Based JWT**: Stateless session management with HTTP-only cookies (`access_token`, `refresh_token`) to safeguard against XSS attacks.
- **Token Blacklisting**: Revokes refresh tokens on logout using server-side blacklisting.
- **Quiz Management (CRUD)**: List quizzes, filter by timeframe (`?period=today`, `?period=7days`), retrieve details, partially update metadata (`title`, `description`), and delete quizzes.
- **Owner Isolation**: Users can only access, modify, or delete their own quizzes (`403 Forbidden` / `404 Not Found` for unauthorized access).
- **Django Admin Panel**: Admin interface with `QuestionInline` support to inspect and edit quizzes and individual questions.

---

## Tech Stack

| Component | Technology | Description |
|:---|:---|:---|
| **Language** | Python 3.12+ / 3.14 | Core programming language |
| **Framework** | Django 6.1 | Web application framework |
| **API Framework** | Django REST Framework 3.18 | RESTful API toolkit |
| **Authentication** | SimpleJWT with Token Blacklist | JWT via HTTP-only cookies |
| **Database** | SQLite (development) | Relational database (PostgreSQL-compatible) |
| **Audio Extraction** | `yt-dlp` & FFmpeg | YouTube audio extraction and MP3 encoding |
| **Transcription** | OpenAI Whisper (`base` model) | Local speech-to-text model |
| **AI Model** | Google Gemini 2.5 Flash (`google-genai`) | AI question and option generator |
| **CORS** | `django-cors-headers` | Cross-Origin Resource Sharing handling |
| **Testing** | Django Test / Coverage | 55 automated unit/integration tests (99% coverage) |
| **Code Style** | PEP-8 / Flake8 | Strict formatting ($\le 14$ lines per function) |

---

## Project Structure

```text
quizly_backend/
├── auth_app/                      # Authentication application
│   ├── api/
│   │   ├── authenticate.py        # Custom CookieJWTAuthentication
│   │   ├── serializers.py         # Registration & login serializers
│   │   ├── urls.py                # Authentication endpoints
│   │   ├── utils.py               # Cookie setting, deletion & token helpers
│   │   └── views.py               # Register, Login, Refresh, Logout views
│   ├── admin.py
│   ├── models.py
│   └── tests.py                   # Automated authentication unit tests
├── quiz_app/                      # Quiz domain & generation pipeline
│   ├── api/
│   │   ├── serializers.py         # Quiz & Question serializers
│   │   ├── urls.py                # Quiz endpoints
│   │   ├── utils.py               # Audio extraction, Whisper, Gemini & validation
│   │   └── views.py               # QuizListCreateView & QuizDetailView
│   ├── admin.py                   # QuizAdmin with QuestionInline
│   ├── models.py                  # Quiz and Question models
│   └── tests.py                   # Automated quiz model & API tests
├── core/                          # Django project configuration
│   ├── settings.py                # Core configuration (JWT, CORS, env variables)
│   ├── urls.py                    # Global URL dispatcher
│   ├── wsgi.py
│   └── asgi.py
├── manage.py                      # Django CLI management script
├── requirements.txt               # Python package dependencies
├── .env.example                   # Template for environment variables
└── README.md                      # Project documentation
```

---

## API Endpoints

All API endpoints are prefixed with `/api/`.

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|:---|:---|:---|:---|
| `POST` | `/api/register/` | Register a new user account (`username`, `email`, `password`, `confirmed_password`) | No |
| `POST` | `/api/login/` | Authenticate user and receive HTTP-only JWT cookies | No |
| `POST` | `/api/token/refresh/` | Obtain a new access token using the refresh cookie | No |
| `POST` | `/api/logout/` | Invalidate the refresh token and clear auth cookies | Yes |

### Quiz Endpoints

| Method | Endpoint | Description | Auth Required |
|:---|:---|:---|:---|
| `GET` | `/api/quizzes/` | List all quizzes belonging to the authenticated user (`?period=today`, `?period=7days`) | Yes |
| `POST` | `/api/quizzes/` | Generate a new quiz from a YouTube URL | Yes |
| `GET` | `/api/quizzes/<id>/` | Retrieve a specific quiz with all questions | Yes |
| `PATCH` | `/api/quizzes/<id>/` | Partially update quiz metadata (`title`, `description`) | Yes |
| `DELETE` | `/api/quizzes/<id>/` | Delete a quiz and all associated questions | Yes |

### Quiz Generation Workflow

Send an authenticated `POST` request to `/api/quizzes/`:

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Step-by-step processing pipeline:**
1. **URL Validation**: Validates that the input is a valid YouTube URL (`youtube.com` or `youtu.be`).
2. **Audio Download**: `yt-dlp` downloads the best available audio stream into a temporary directory.
3. **FFmpeg Conversion**: Transcodes the audio to MP3 format.
4. **Whisper Transcription**: OpenAI Whisper (`base` model) transcribes the speech to text.
5. **Gemini AI Prompting**: Google Gemini 2.5 Flash analyzes the transcript and outputs a structured quiz.
6. **Data Validation & Persistence**: Validates that exactly 10 questions with 4 distinct options each and 1 matching correct answer were generated, then saves the quiz and questions to the database linked to the user.
7. **Cleanup**: Deletes temporary audio files from disk.

---

## Authentication Architecture

Quizly Backend uses JSON Web Tokens (JWT) transmitted via secure, HTTP-only cookies:

- **Login**: Sets `access_token` and `refresh_token` as HTTP-only cookies.
- **Protected Requests**: [CookieJWTAuthentication](file:///c:/Users/mario/Desktop/quizly_backend/auth_app/api/authenticate.py) inspects incoming requests for the `access_token` cookie (with automatic fallback to the `Authorization: Bearer <token>` header).
- **Token Refresh**: The `/api/token/refresh/` endpoint reads the `refresh_token` cookie and issues a fresh `access_token` cookie.
- **Logout**: The `/api/logout/` endpoint blacklists the refresh token in the database and clears all authentication cookies.

---

## Testing & Quality Assurance

The project comes with a comprehensive test suite covering models, views, permissions, serializers, and utility functions:

### 1. System Check
```bash
python manage.py check
```

### 2. Run Test Suite
```bash
python manage.py test
```

### 3. Run Coverage Report
```bash
coverage run --source='auth_app,quiz_app' manage.py test
coverage report
```
> **Test Results**: **55 of 55 tests passing**, **99% total coverage** across `auth_app` and `quiz_app`.

### 4. Run PEP-8 Linter
```bash
flake8 --exclude=.venv,migrations .
```
> **Linting Results**: **0 errors, 0 warnings**.

---

## Code Conventions & Clean Code Standards

- **Maximum Function Length**: Every function and method is strictly **$\le 14$ lines long**.
- **Single Responsibility Principle (SRP)**: Each function performs exactly one well-defined task.
- **Naming Conventions**: Strict `snake_case` for functions/variables and `PascalCase` for classes.
- **Clean Django Architecture**:
  - `views.py`: Request handling and response returns only.
  - `utils.py`: Reusable business logic, AI orchestration, and helper functions.
  - `serializers.py`: Data serialization, deserialization, and validation.
- **Documentation**: Comprehensive docstrings on all modules, classes, and methods.
- **Zero Dead Code**: No commented-out code blocks or orphan `print()` statements.

---

## Notes for Local Development

- **Local Database**: The local SQLite database (`db.sqlite3`) is excluded from version control. Run `python manage.py migrate` to initialize a fresh database.
- **Environment Variables**: Sensitive secrets in `.env` are never committed to Git. Keep your `GEMINI_API_KEY` private.
- **FFmpeg**: Must be installed on your operating system and available in the system `PATH`.
- **Whisper Model**: Uses the `base` model. On the first run, model weights are downloaded and cached automatically.
- **Synchronous Execution**: Quiz generation runs synchronously within the request. For production environments with longer videos, consider offloading generation to an asynchronous worker queue (such as Celery or Django Q).
