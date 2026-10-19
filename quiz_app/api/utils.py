"""Utility functions for audio processing, AI quiz generation, and data."""
from datetime import timedelta
import json
import os
import tempfile

from django.utils import timezone
from google import genai
from google.genai import types
import whisper
import yt_dlp

from quiz_app.models import Question, Quiz

QUIZ_PROMPT_TEMPLATE = (
    "Based on the following transcript, generate a quiz in JSON format.\n"
    "The quiz must follow this exact structure:\n"
    "{{\n"
    '  "title": "Concise quiz title based on the transcript.",\n'
    '  "description": "Short summary of the transcript (max 150 chars).",\n'
    '  "questions": [\n'
    "    {{\n"
    '      "question_title": "The question text.",\n'
    '      "question_options": [\n'
    '        "Option A", "Option B", "Option C", "Option D"\n'
    '      ],\n'
    '      "answer": "The correct answer from question_options"\n'
    "    }}\n"
    "  ]\n"
    "}}\n"
    "Requirements:\n"
    "- Generate exactly 10 questions.\n"
    "- Each question must have exactly 4 distinct answer options.\n"
    "- Only one correct answer per question, matching one option exactly.\n"
    "- Output must be strictly valid JSON without markdown code blocks.\n\n"
    "Transcript:\n{transcript}"
)


def get_yt_dlp_options(template):

    """Return yt_dlp configuration dictionary for MP3 audio extraction."""
    return {
        'format': 'bestaudio/best',
        'outtmpl': template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True,
    }


def download_audio_from_youtube(url, target_dir):
    """Download audio track from a YouTube URL into target directory."""
    template = os.path.join(target_dir, '%(id)s.%(ext)s')
    opts = get_yt_dlp_options(template)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return os.path.join(target_dir, f"{info['id']}.mp3")


def transcribe_audio_file(audio_path):
    """Transcribe an audio file and return its recognized text."""
    model = whisper.load_model('base')
    result = model.transcribe(audio_path)
    return result.get('text', '')


def clean_markdown_json_response(raw_text):
    """Remove optional Markdown code fences from a JSON response."""
    text = raw_text.strip()
    if text.startswith('```json'):
        text = text[7:]
    elif text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    return text.strip()


def request_gemini_quiz_content(client, prompt):
    """Send prompt to Gemini model and return response text."""
    config = types.GenerateContentConfig(response_mime_type="application/json")
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt, config=config
    )
    return response.text


def generate_quiz_payload(transcript):
    """Generate and parse quiz data from an audio transcript."""
    client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
    prompt = QUIZ_PROMPT_TEMPLATE.format(transcript=transcript)
    raw_response = request_gemini_quiz_content(client, prompt)
    cleaned_json = clean_markdown_json_response(raw_response)
    return json.loads(cleaned_json)


def save_quiz_record(user, url, quiz_data):
    """Create and return a quiz record from generated quiz data."""
    return Quiz.objects.create(
        user=user,
        video_url=url,
        title=quiz_data.get('title', 'Neues Quiz'),
        description=quiz_data.get('description', ''),
    )


def save_quiz_questions(quiz, questions_data):
    """Create question records for a quiz from generated question data."""
    for item in questions_data:
        Question.objects.create(
            quiz=quiz,
            question_title=item.get('question_title'),
            question_options=item.get('question_options', []),
            answer=item.get('answer'),
        )


def delete_file_safely(file_path):
    """Remove the specified file if it exists."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)


def process_youtube_quiz_creation(user, url):
    """Create a quiz from a YouTube video and remove its temporary audio."""
    temp_dir = tempfile.gettempdir()
    audio_path = download_audio_from_youtube(url, temp_dir)
    try:
        transcript = transcribe_audio_file(audio_path)
        quiz_data = generate_quiz_payload(transcript)
        quiz = save_quiz_record(user, url, quiz_data)
        save_quiz_questions(quiz, quiz_data.get('questions', []))
        return quiz
    finally:
        delete_file_safely(audio_path)


def get_user_quiz_or_status(quiz_id, user):
    """Return a quiz owned by the user and its HTTP status code."""
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        return None, 404
    if quiz.user != user:
        return None, 403
    return quiz, 200


def filter_user_quizzes(user, period=None):
    """Return user quizzes optionally filtered by timeframe (today, 7days)."""
    queryset = Quiz.objects.filter(user=user)
    if period == 'today':
        return queryset.filter(created_at__date=timezone.now().date())
    if period in ('7days', 'last_7_days', 'week'):
        start_date = timezone.now() - timedelta(days=7)
        return queryset.filter(created_at__gte=start_date)
    return queryset
