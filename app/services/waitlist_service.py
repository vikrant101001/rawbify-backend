from sqlalchemy.orm import Session
from ..models.waitlist import Waitlist
from ..schemas.waitlist import WaitlistCreate
from ..config import settings
import re
import smtplib
from email.message import EmailMessage

EMAIL_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Welcome to Rawbify Waitlist</title>
</head>
<body style="font-family: Arial, sans-serif; background: #f8fafc; margin: 0; padding: 0;">
  <table width="100%" bgcolor="#f8fafc" cellpadding="0" cellspacing="0" style="padding: 32px 0;">
    <tr>
      <td align="center">
        <table width="100%" bgcolor="#fff" cellpadding="0" cellspacing="0" style="max-width: 480px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); overflow: hidden;">
          <tr>
            <td align="center" style="padding: 32px 24px 16px 24px;">
              <img src="https://raw.githubusercontent.com/vikramaditya91/rawbify-assets/main/rawbify_logo.svg" alt="Rawbify Logo" width="64" height="64" style="margin-bottom: 16px;" />
              <h2 style="color: #2563eb; margin: 0 0 8px 0; font-size: 1.5rem;">Welcome to the Rawbify Waitlist!</h2>
              <p style="color: #334155; font-size: 1rem; margin: 0 0 16px 0;">Thank you for joining the waitlist. We're excited to have you on board!</p>
              <div style="background: #f1f5f9; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <p style="color: #64748b; font-size: 0.95rem; margin: 0 0 8px 0;">Your Waitlist ID:</p>
                <div style="font-size: 1.1rem; font-weight: bold; color: #2563eb; letter-spacing: 1px;">{waitlist_id}</div>
              </div>
              <p style="color: #334155; font-size: 1rem; margin: 0 0 16px 0;">Trial V1 is coming soon! You will be notified via email as soon as it's ready for you to try.</p>
              <a href="https://rawbify.com" style="display: inline-block; background: #2563eb; color: #fff; text-decoration: none; padding: 12px 32px; border-radius: 6px; font-weight: 600; margin-top: 12px;">Visit Rawbify</a>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding: 16px 24px 24px 24px; color: #94a3b8; font-size: 0.9rem;">
              &copy; 2024 Rawbify. All rights reserved.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
'''

class WaitlistService:
    @staticmethod
    def add_to_waitlist(db: Session, email: str) -> dict:
        """Add email to waitlist and send a beautiful email"""
        try:
            # Check if email already exists
            existing = db.query(Waitlist).filter(Waitlist.email == email).first()
            if existing:
                return {
                    "success": False,
                    "message": "Email already on waitlist",
                    "waitlist_count": None
                }
            
            # Add new email to waitlist
            new_waitlist = Waitlist(email=email)
            db.add(new_waitlist)
            db.commit()
            db.refresh(new_waitlist)
            
            # Send email
            WaitlistService.send_waitlist_email(email, new_waitlist.id)
            
            # Get total count
            total_count = db.query(Waitlist).count()
            
            return {
                "success": True,
                "message": "Successfully added to waitlist and email sent!",
                "waitlist_count": total_count
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "message": f"Error adding to waitlist: {str(e)}",
                "waitlist_count": None
            }
    
    @staticmethod
    def send_waitlist_email(to_email: str, waitlist_id: str):
        if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
            raise Exception("Gmail credentials not set in environment variables.")
        msg = EmailMessage()
        msg['Subject'] = "You're on the Rawbify Waitlist!"
        msg['From'] = f"Rawbify <{settings.GMAIL_USER}>"
        msg['To'] = to_email
        msg.set_content("This email requires HTML support.")
        msg.add_alternative(EMAIL_TEMPLATE.format(waitlist_id=waitlist_id), subtype='html')
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
    
    @staticmethod
    def get_waitlist_stats(db: Session) -> dict:
        """Get waitlist statistics"""
        try:
            total_count = db.query(Waitlist).count()
            return {
                "success": True,
                "message": "Waitlist stats retrieved",
                "waitlist_count": total_count
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting stats: {str(e)}",
                "waitlist_count": None
            } 