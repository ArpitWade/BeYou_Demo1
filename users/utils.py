# users/utils.py
import random
from django.utils import timezone
import datetime
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp_email(user, otp):
    subject = 'Email Verification OTP'
    message = f'Hi {user.username}, here is your OTP for email verification: {otp}. This OTP will expire in 5 minutes.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)

def create_otp_for_user(user):
    from .models import OTP
    
    # Delete any existing OTPs for this user
    OTP.objects.filter(user=user).delete()
    
    otp_code = generate_otp()
    expires_at = timezone.now() + datetime.timedelta(minutes=5)
    otp_obj = OTP.objects.create(user=user, otp=otp_code, expires_at=expires_at)
    
    # Send the OTP via email
    send_otp_email(user, otp_code)
    
    return otp_obj
