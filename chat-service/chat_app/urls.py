from django.urls import path
from .views import (
    ChatHistoryView,
    MarkChatReadView,
    UnreadCountView,
    VendorInboxView,
)

urlpatterns = [
    path("messages/", ChatHistoryView.as_view()),
    path("mark-read/", MarkChatReadView.as_view()),
    path("unread-count/", UnreadCountView.as_view()),
    path("inbox/", VendorInboxView.as_view()),
]
