# users/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated  # Add this import
from .serializers import UserRegistrationSerializer, OTPVerificationSerializer
from .models import User, OTP, Report  # Add Report model import
from .utils import create_otp_for_user

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate OTP and send via email
            create_otp_for_user(user)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'User registered successfully. Please check your email for OTP verification.',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OTPVerificationView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        
        if serializer.is_valid():
            otp_code = serializer.validated_data['otp']
            
            try:
                # Get the user from the token
                user = request.user
                otp_obj = OTP.objects.filter(user=user, otp=otp_code).first()
                
                if not otp_obj:
                    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
                
                if otp_obj.is_expired():
                    return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Mark user as verified
                user.is_verified = True
                user.save()
                
                # Delete the OTP
                otp_obj.delete()
                
                return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    def post(self, request):
        user = request.user
        
        if user.is_verified:
            return Response({'message': 'User is already verified'}, status=status.HTTP_400_BAD_REQUEST)
        
        create_otp_for_user(user)
        
        return Response({'message': 'New OTP sent successfully'}, status=status.HTTP_200_OK)

# users/views.py
from friendship.models import Friend, Follow, FriendshipRequest, Block
from friendship.exceptions import AlreadyExistsError

class FriendRequestView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, to_user_id):
        try:
            to_user = User.objects.get(id=to_user_id)
            
            # Check if the user is trying to friend themselves
            if request.user == to_user:
                return Response({'error': 'You cannot send a friend request to yourself'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if a friendship already exists
            if Friend.objects.are_friends(request.user, to_user):
                return Response({'error': 'You are already friends with this user'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if the user is blocked
            if Block.objects.is_blocked(request.user, to_user):
                return Response({'error': 'You cannot send a friend request to a blocked user'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Send friend request
            try:
                Friend.objects.add_friend(request.user, to_user, message=request.data.get('message', ''))
                return Response({'message': 'Friend request sent successfully'}, status=status.HTTP_201_CREATED)
            except AlreadyExistsError:
                return Response({'error': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)
                
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class FriendRequestActionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, request_id):
        try:
            friendship_request = FriendshipRequest.objects.get(id=request_id, to_user=request.user)
            action = request.data.get('action')
            
            if action == 'accept':
                friendship_request.accept()
                return Response({'message': 'Friend request accepted'}, status=status.HTTP_200_OK)
            elif action == 'reject':
                friendship_request.reject()
                return Response({'message': 'Friend request rejected'}, status=status.HTTP_200_OK)
            elif action == 'cancel':
                friendship_request.cancel()
                return Response({'message': 'Friend request canceled'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
                
        except FriendshipRequest.DoesNotExist:
            return Response({'error': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)


# users/views.py
class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, to_user_id):
        try:
            to_user = User.objects.get(id=to_user_id)
            
            # Check if the user is trying to follow themselves
            if request.user == to_user:
                return Response({'error': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if already following
            if Follow.objects.follows(request.user, to_user):
                return Response({'error': 'You are already following this user'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Follow the user
            Follow.objects.add_follower(request.user, to_user)
            
            return Response({'message': 'User followed successfully'}, status=status.HTTP_201_CREATED)
                
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, to_user_id):
        try:
            to_user = User.objects.get(id=to_user_id)
            
            # Check if following
            if not Follow.objects.follows(request.user, to_user):
                return Response({'error': 'You are not following this user'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Unfollow the user
            Follow.objects.remove_follower(request.user, to_user)
            
            return Response({'message': 'User unfollowed successfully'}, status=status.HTTP_200_OK)
                
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


# users/views.py
class BlockUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, to_user_id):
        try:
            to_user = User.objects.get(id=to_user_id)
            
            # Check if the user is trying to block themselves
            if request.user == to_user:
                return Response({'error': 'You cannot block yourself'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if already blocked
            if Block.objects.is_blocked(request.user, to_user):
                return Response({'error': 'You have already blocked this user'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Block the user
            Block.objects.add_block(request.user, to_user)
            
            # Remove any friendship
            if Friend.objects.are_friends(request.user, to_user):
                Friend.objects.remove_friend(request.user, to_user)
            
            # Remove any follow relationship
            if Follow.objects.follows(request.user, to_user):
                Follow.objects.remove_follower(request.user, to_user)
            
            return Response({'message': 'User blocked successfully'}, status=status.HTTP_201_CREATED)
                
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, to_user_id):
        try:
            to_user = User.objects.get(id=to_user_id)
            
            # Check if blocked
            if not Block.objects.is_blocked(request.user, to_user):
                return Response({'error': 'This user is not blocked'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Unblock the user
            Block.objects.remove_block(request.user, to_user)
            
            return Response({'message': 'User unblocked successfully'}, status=status.HTTP_200_OK)
                
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


# users/views.py
class ReportUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, to_user_id):
        try:
            to_user = User.objects.get(id=to_user_id)
            
            # Check if the user is trying to report themselves
            if request.user == to_user:
                return Response({'error': 'You cannot report yourself'}, status=status.HTTP_400_BAD_REQUEST)
            
            reason = request.data.get('reason')
            details = request.data.get('details', '')
            
            if not reason:
                return Response({'error': 'Reason is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the report
            Report.objects.create(
                reporter=request.user,
                reported_user=to_user,
                reason=reason,
                details=details
            )
            
            return Response({'message': 'User reported successfully'}, status=status.HTTP_201_CREATED)
                
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

