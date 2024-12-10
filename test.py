import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Load the SENDGRID_API_KEY from the environment
sendgrid_api_key = os.getenv('SENDGRID_API_KEY')

# Test the SendGrid API client initialization
try:
    sg = SendGridAPIClient(api_key=sendgrid_api_key)
    print(f"SendGrid API client initialized successfully. Version: {sg.client.version}")
except Exception as e:
    print(f"Error initializing SendGrid API client: {e}")

# Test sending an email
try:
    message = Mail(
        from_email='danielnsanzabandi@gmail.com',
        to_emails=['nsanzabandidani@gmail.com'],
        subject='Test email',
        html_content='<strong>Hello, philemon!</strong>')
    response = sg.send(message)
    print(f"Email sent successfully. Response status code: {response.status_code}")
except Exception as e:
    print(f"Error sending email: {e}")