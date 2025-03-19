from django.urls import path
from .views import (
    UserRegistrationView, OTPVerificationView, ResendOTPView,
    FriendRequestView, FriendRequestActionView, FollowUserView,
    BlockUserView, ReportUserView, ProfileView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-otp/', OTPVerificationView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/<int:user_id>/', ProfileView.as_view(), name='user-profile'),
    
    # Friend Requests
    path('friend-request/<int:to_user_id>/', FriendRequestView.as_view(), name='friend-request'),
    path('friend-request-action/<int:request_id>/', FriendRequestActionView.as_view(), name='friend-request-action'),
    
    # Follow/Unfollow
    path('follow/<int:to_user_id>/', FollowUserView.as_view(), name='follow-user'),
    
    # Block/Report
    path('block/<int:to_user_id>/', BlockUserView.as_view(), name='block-user'),
    path('report/<int:to_user_id>/', ReportUserView.as_view(), name='report-user'),
]
