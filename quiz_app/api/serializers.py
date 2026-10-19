"""Serializers for quiz and question data structures."""
from rest_framework import serializers

from quiz_app.models import Question, Quiz


class QuestionSerializer(serializers.ModelSerializer):
    """Serialize quiz question details."""

    class Meta:
        model = Question
        fields = [
            'id',
            'question_title',
            'question_options',
            'answer',
            'created_at',
            'updated_at',
        ]


class QuizSerializer(serializers.ModelSerializer):
    """Serialize quiz details along with their questions."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id',
            'title',
            'description',
            'created_at',
            'updated_at',
            'video_url',
            'questions',
        ]


class QuizUpdateSerializer(serializers.ModelSerializer):
    """Validate and serialize fields that can be updated on a quiz."""

    class Meta:
        model = Quiz
        fields = ['title', 'description']
