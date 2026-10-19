"""API views for listing, creating, retrieving, and updating quizzes."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import QuizSerializer, QuizUpdateSerializer
from .utils import (
    filter_user_quizzes,
    get_user_quiz_or_status,
    process_youtube_quiz_creation,
)


class QuizListCreateView(generics.ListCreateAPIView):
    """List quizzes or generate a new quiz from a YouTube URL."""

    permission_classes = [IsAuthenticated]

    serializer_class = QuizSerializer

    def get_queryset(self):
        """Return quizzes owned by the user, optionally filtered by period."""
        period = self.request.query_params.get('period')
        return filter_user_quizzes(self.request.user, period)

    def create(self, request, *args, **kwargs):
        """Generate and persist a new quiz from a provided YouTube URL."""
        url = request.data.get('url')
        if not url:
            return Response(
                {'detail': 'YouTube URL is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        quiz = process_youtube_quiz_creation(request.user, url)
        serializer = self.get_serializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizDetailView(APIView):
    """Retrieve, update, or delete a specific quiz owned by the user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Retrieve a specific quiz by its primary key."""
        quiz, code = get_user_quiz_or_status(pk, request.user)
        if not quiz:
            return Response({'detail': 'Not found or forbidden.'}, status=code)
        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """Update the title or description of a quiz."""
        quiz, code = get_user_quiz_or_status(pk, request.user)
        if not quiz:
            return Response({'detail': 'Not found or forbidden.'}, status=code)
        serializer = QuizUpdateSerializer(
            quiz, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """Delete an existing quiz owned by the current user."""
        quiz, code = get_user_quiz_or_status(pk, request.user)
        if not quiz:
            return Response({'detail': 'Not found or forbidden.'}, status=code)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
