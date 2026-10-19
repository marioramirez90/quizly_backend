"""Admin panel configuration for managing quizzes and individual questions."""
from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.TabularInline):
    """Inline editor for questions within a quiz detail view."""

    model = Question
    extra = 0
    fields = ('question_title', 'question_options', 'answer')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin configuration for viewing and editing quizzes."""

    list_display = ('id', 'title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'user')
    search_fields = ('title', 'description', 'video_url')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin configuration for viewing and editing individual questions."""

    list_display = ('id', 'question_title', 'quiz', 'answer', 'created_at')
    list_filter = ('created_at', 'quiz')
    search_fields = ('question_title', 'answer')
    readonly_fields = ('created_at', 'updated_at')
