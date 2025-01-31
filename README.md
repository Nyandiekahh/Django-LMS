# Learnify - Modern Learning Management System

A comprehensive Learning Management System built with Django, designed to streamline educational institution management and enhance the learning experience.

## Features

- Multi-user Roles (Admin, Lecturer, Student)
- Interactive Dashboard with Analytics
- Course Management System
- Student Grade Management
- Real-time Assessment & Quiz System
- PDF Report Generation
- Video Content Management
- Session & Semester Management

## Modules

### For Administrators
- Complete User Management
- Course Allocation
- Session/Semester Control
- System Analytics
- Performance Monitoring

### For Lecturers
- Course Management
- Student Assessment
- Grade Submission
- Content Upload
- Quiz Management

### For Students
- Course Registration
- Grade Access
- Assessment Results
- Course Materials Access
- Quiz Participation

## Technical Requirements

- Python 3.8+
- Django
- Other dependencies in requirements.txt

## Installation

1. Clone the repository
```bash
git clone https://github.com/Nyandiekahh/Django-LMS.git

Create and activate virtual environment

bashCopypython -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

Install dependencies

bashCopypip install -r requirements.txt

Set up environment variables


Create .env file in root directory
Configure your environment variables


Run migrations

bashCopypython manage.py migrate

Create superuser

bashCopypython manage.py createsuperuser

Start development server

bashCopypython manage.py runserver
Visit http://127.0.0.1:8000 to access the application
Contact
For inquiries or support, reach out to the developer:
Portfolio
License
This project is licensed under the MIT License - see the LICENSE file for details