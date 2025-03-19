from django.urls import path
from .views import (
    ChatRoomListCreateView, ChatRoomDetailView,
    MessageListView, FileUploadView
)

urlpatterns = [
    path('rooms/', ChatRoomListCreateView.as_view(), name='chat-rooms'),
    path('rooms/<int:room_id>/', ChatRoomDetailView.as_view(), name='chat-room-detail'),
    path('rooms/<int:room_id>/messages/', MessageListView.as_view(), name='chat-messages'),
    path('rooms/<int:room_id>/upload/', FileUploadView.as_view(), name='file-upload'),
]
