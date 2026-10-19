"""API views for listing, creating, retrieving, and updating quizzes."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import QuizSerializer, QuizUpdateSerializer
from .utils import (
    create_quiz_from_youtube_url,
    filter_user_quizzes,
    get_user_quiz_or_error,
    is_valid_youtube_url,
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
        if not is_valid_youtube_url(url):
            msg = {'detail': 'Ungültige URL oder Anfragedaten.'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        quiz, err = create_quiz_from_youtube_url(request.user, url.strip())
        if err:
            return Response(
                {'detail': err}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizDetailView(APIView):
    """Retrieve, update, or delete a specific quiz owned by the user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Retrieve a specific quiz by its primary key."""
        quiz, code, err = get_user_quiz_or_error(pk, request.user)
        if err:
            return Response({'detail': err}, status=code)
        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """Update the title or description of a quiz."""
        quiz, code, err = get_user_quiz_or_error(pk, request.user)
        if err:
            return Response({'detail': err}, status=code)
        serializer = QuizUpdateSerializer(
            quiz, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """Delete an existing quiz owned by the current user."""
        quiz, code, err = get_user_quiz_or_error(pk, request.user)
        if err:
            return Response({'detail': err}, status=code)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
