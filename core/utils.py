import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.utils.text import slugify
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_email(user, subject, msg):
   msg = MIMEText(msg)
   msg['Subject'] = subject
   msg['From'] = settings.EMAIL_FROM_ADDRESS
   msg['To'] = user.email
   
   with smtplib.SMTP('smtp.gmail.com', 587) as server:
       server.starttls()
       server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
       server.send_message(msg)

def send_html_email(subject, recipient_list, template, context):
   html_message = render_to_string(template, context)
   plain_message = strip_tags(html_message)
   
   msg = MIMEMultipart('alternative')
   msg['Subject'] = subject
   msg['From'] = settings.EMAIL_FROM_ADDRESS
   msg['To'] = ', '.join(recipient_list)
   
   msg.attach(MIMEText(plain_message, 'plain'))
   msg.attach(MIMEText(html_message, 'html'))
   
   with smtplib.SMTP('smtp.gmail.com', 587) as server:
       server.starttls()
       server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
       server.send_message(msg)

def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
   return "".join(random.choice(chars) for _ in range(size))

def unique_slug_generator(instance, new_slug=None):
   if new_slug is not None:
       slug = new_slug
   else:
       slug = slugify(instance.title)

   klass = instance.__class__
   qs_exists = klass.objects.filter(slug=slug).exists()
   if qs_exists:
       new_slug = f"{slug}-{random_string_generator(size=4)}"
       return unique_slug_generator(instance, new_slug=new_slug)
   return slug