from django.urls import path

from .views import AskRAGView


urlpatterns = [
    path("ask/", AskRAGView.as_view(), name="rag-ask"),
]
