import smtplib
from email.mime.text import MIMEText

sender = "learnifylms2025@gmail.com"
password = "gsnk jfro vdwd fnwp"
recipient = "test@example.com"

msg = MIMEText("Test email")
msg['Subject'] = "Test Subject"
msg['From'] = sender
msg['To'] = recipient

try:
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        print("Email sent successfully")
except Exception as e:
    print(f"Error: {e}")
