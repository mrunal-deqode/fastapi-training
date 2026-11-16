import asyncio
from celery_app import celery_app
from utils.email_service import send_email


@celery_app.task(name="tasks.send_application_status_notification")
def send_application_status_email(email: str, name: str, job_title: str, application_status: str):
    subject = f"Application Update - {job_title}"

    body = f"""
    Hello {name},

    We have an update regarding your job application.

    Job Title: {job_title}
    Current Application Status: {application_status}

    Please log in to your Recruitment & Hiring account
    to check your application details.

    Thank you,
    Recruitment & Hiring Team
    """

    asyncio.run(send_email(recipient=email, subject=subject, body=body))
