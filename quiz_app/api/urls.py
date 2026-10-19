"""URL routing configuration for quiz endpoints."""
from django.urls import path

from .views import QuizDetailView, QuizListCreateView

urlpatterns = [
    path('quizzes/', QuizListCreateView.as_view(), name='quiz_list_create'),
    path('quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz_detail'),
]
