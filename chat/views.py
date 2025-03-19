# chat/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .models import ChatRoom, Message
import os

class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id, members=request.user)
            file = request.FILES.get('file')
            
            if not file:
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create a new message with the uploaded file
            message = Message.objects.create(
                room=room,
                sender=request.user,
                file=file,
                file_name=file.name
            )
            
            # Get the file URL
            file_url = request.build_absolute_uri(settings.MEDIA_URL + str(message.file))
            
            # Send the file message via channels
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            room_group_name = f'chat_{room_id}'
            
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'chat_message',
                    'message': '',
                    'user_id': request.user.id,
                    'message_id': message.id,
                    'file_url': file_url,
                    'file_name': file.name
                }
            )
            
            return Response({
                'message_id': message.id,
                'file_url': file_url,
                'file_name': file.name
            }, status=status.HTTP_201_CREATED)
            
        except ChatRoom.DoesNotExist:
            return Response({'error': 'Chat room not found or you do not have access'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
