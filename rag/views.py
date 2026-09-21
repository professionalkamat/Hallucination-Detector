from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .local_rag import answer


class AskRAGView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = str(request.data.get("question", "")).strip()
        if not question:
            return Response({"error": "question is required"}, status=400)

        try:
            return Response(answer(question))
        except RuntimeError as exc:
            return Response({"error": str(exc)}, status=503)
        except Exception:
            return Response(
                {"error": "The RAG service is unavailable. Check API credentials and ChromaDB."},
                status=503,
            )
