# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            message = data['message']
            user_id = self.scope['user'].id
            
            # Save message to database
            message_id = await self.save_message(user_id, message)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user_id': user_id,
                    'message_id': message_id,
                }
            )
        
        elif message_type == 'typing':
            user_id = self.scope['user'].id
            username = self.scope['user'].username
            is_typing = data['is_typing']
            
            # Send typing status to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': user_id,
                    'username': username,
                    'is_typing': is_typing
                }
            )
    
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'user_id': event['user_id'],
            'message_id': event['message_id'],
        }))
    
    async def user_typing(self, event):
        # Send typing status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    
    @database_sync_to_async
    def save_message(self, user_id, message):
        user = User.objects.get(id=user_id)
        room = ChatRoom.objects.get(id=self.room_id)
        message_obj = Message.objects.create(
            room=room,
            sender=user,
            content=message
        )
        return message_obj.id
