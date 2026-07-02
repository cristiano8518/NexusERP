from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import ask_ollama


class AiChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = (request.data.get("message") or "").strip()
        if not message:
            return Response(
                {"success": False, "detail": "Сұрақ мәтінін енгізіңіз."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(message) > 2000:
            return Response(
                {"success": False, "detail": "Сұрақ тым ұзын. 2000 таңбадан асырмаңыз."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = ask_ollama(message, request.user)
        return Response(result, status=status.HTTP_200_OK)
