from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from quiz_app.models import Quiz
from .serializers import QuizSerializer, QuizUpdateSerializer
from .utils import get_user_quiz_or_status, process_youtube_quiz_creation


class QuizListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizSerializer

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
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
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        quiz, code = get_user_quiz_or_status(pk, request.user)
        if not quiz:
            return Response({'detail': 'Not found or forbidden.'}, status=code)
        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        quiz, code = get_user_quiz_or_status(pk, request.user)
        if not quiz:
            return Response({'detail': 'Not found or forbidden.'}, status=code)
        serializer = QuizUpdateSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        quiz, code = get_user_quiz_or_status(pk, request.user)
        if not quiz:
            return Response({'detail': 'Not found or forbidden.'}, status=code)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)