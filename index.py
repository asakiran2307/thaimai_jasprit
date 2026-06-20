import os
import json
import time, operator
import base64
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Flask and Web-related imports
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import BaseLoader, TemplateNotFound

# Backend Feature Imports
import requests
from geopy.distance import geodesic

# PDF processing
from pypdf import PdfReader, errors as pypdf_errors

# ==============================================================================
# 1. HTML TEMPLATES (EMBEDDED AS STRINGS)
# ==============================================================================

LAYOUT_HTML = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Maternal Care Portal{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="icon" href="{{ url_for('static', filename='logo.png') }}">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">    
    <style>
        :root {
            --primary-pink: #E895A7;
            --soft-pink: #FDECF0;
            --dark-text: #5D5D5D;
            --light-text: #f8f9fa;
            --light-bg: #fcf7f8;
            --dark-bg: #2c3e50;
            --glass-bg-light: rgba(255, 255, 255, 0.5);
            --glass-bg-dark: rgba(44, 62, 80, 0.6);
            --border-light: rgba(232, 149, 167, 0.3);
            --border-dark: rgba(253, 236, 240, 0.3);
            --primary-color-rgb: 232, 149, 167;
        }

        [data-bs-theme="light"] {
            --bs-primary: var(--primary-pink);
            --bs-primary-rgb: var(--primary-color-rgb);
            --bs-body-bg: var(--light-bg);
            --bs-body-color: var(--dark-text);
            --glass-bg: var(--glass-bg-light);
            --card-border-color: var(--border-light);
            --background-gradient: linear-gradient(135deg, #fdecf0 0%, #f7d8e1 100%);
        }

        [data-bs-theme="dark"] {
            --bs-primary: var(--primary-pink);
            --bs-primary-rgb: var(--primary-color-rgb);
            --bs-body-bg: var(--dark-bg);
            --bs-body-color: var(--light-text);
            --glass-bg: var(--glass-bg-dark);
            --card-border-color: var(--border-dark);
            --background-gradient: linear-gradient(135deg, #2c3e50 0%, #465869 100%);
        }

        body {
            font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
            transition: background 0.4s ease;
            min-height: 100vh;
            background: var(--background-gradient);
            background-size: 200% 200%;
            animation: gradient-animation 15s ease infinite;
        }

        /* Glassmorphism Card Style */
        .card {
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid var(--card-border-color);
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }

        .navbar {
            background: var(--glass-bg) !important;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--card-border-color);
            box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
        }

        .btn, .nav-link, .list-group-item {
            transition: all 0.3s ease;
        }

        .theme-switcher {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }
        .theme-switcher .btn {
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--card-border-color);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        /* Page content animation */
        main.container {
            animation: popIn 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
        }

        @keyframes popIn {
            from { opacity: 0; transform: translateY(20px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        @keyframes gradient-animation {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-white border-bottom">
        <div class="container-fluid">
            <a class="navbar-brand d-flex align-items-center" href="{{ url_for('home') }}">
                <img src="{{ url_for('static', filename='logo.png') }}" alt="Logo" width="28" height="28" class="d-inline-block align-text-top me-2">
                <span style="font-weight: 600;">Maternal Care</span>
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    {% if current_user.is_authenticated %}
                        {% if session.user_type == 'patient' %}
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('patient_dashboard') }}">Dashboard</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('patient_consultant') }}">AI Consultant</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('patient_report_summary') }}">Report Summary</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('patient_appointments') }}">Appointments</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('messages') }}">Messages</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('resources') }}">Resources</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('digital_doula') }}">Digital Doula</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('patient_wellness_log') }}">Wellness Log</a></li>
                            <li class="nav-item"><a class="nav-link text-danger fw-bold" href="{{ url_for('patient_emergency') }}">Emergency</a></li>
                        {% elif session.user_type == 'doctor' %}
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('doctor_dashboard') }}">Dashboard</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('doctor_appointments') }}">Appointments</a></li>
                            <li class="nav-item"><a class="nav-link" href="{{ url_for('doctor_add_patient') }}">Add Patient</a></li>
                        {% endif %}
                        <li class="nav-item dropdown">
                            <a class="nav-link" href="#" id="notifications-dropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="bi bi-bell-fill"></i>
                                <span id="notification-badge" class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger" style="display: none;"></span>
                            </a>
                            <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="notifications-dropdown" id="notifications-list">
                                <!-- Notifications will be loaded here -->
                                <li><p class="dropdown-item text-muted text-center">No new notifications</p></li>
                            </ul>
                        </li>
                        <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}">Logout</a></li>
                    {% else %}
                        <li class="nav-item"><a class="nav-link" href="{{ url_for('login_chooser') }}">Login</a></li>
                    {% endif %}
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('register_patient') }}">Register</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <main class="container my-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </main>

    <div class="theme-switcher">
        <button class="btn" id="theme-toggle-btn">
            <i class="bi bi-moon-stars-fill"></i>
        </button>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const themeToggleBtn = document.getElementById('theme-toggle-btn');
            const htmlEl = document.documentElement;

            const currentTheme = localStorage.getItem('theme') || 'light';
            htmlEl.setAttribute('data-bs-theme', currentTheme);
            themeToggleBtn.innerHTML = currentTheme === 'dark' ? '<i class="bi bi-sun-fill"></i>' : '<i class="bi bi-moon-stars-fill"></i>';

            themeToggleBtn.addEventListener('click', () => {
                const newTheme = htmlEl.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
                htmlEl.setAttribute('data-bs-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                themeToggleBtn.innerHTML = newTheme === 'dark' ? '<i class="bi bi-sun-fill"></i>' : '<i class="bi bi-moon-stars-fill"></i>';
            });

            {% if current_user.is_authenticated %}
            const notificationsList = document.getElementById('notifications-list');
            const notificationBadge = document.getElementById('notification-badge');

            async function fetchNotifications() {
                try {
                    const response = await fetch("{{ url_for('get_notifications') }}");
                    const data = await response.json();
                    
                    notificationsList.innerHTML = '';
                    if (data.notifications.length > 0) {
                        let unreadCount = 0;
                        data.notifications.forEach(n => {
                            if (!n.is_read) unreadCount++;
                            const li = document.createElement('li');
                            li.innerHTML = `<a class="dropdown-item ${!n.is_read ? 'fw-bold' : ''}" href="${n.link_url}">${n.message}</a>`;
                            notificationsList.appendChild(li);
                        });
                        if (unreadCount > 0) {
                            notificationBadge.textContent = unreadCount;
                            notificationBadge.style.display = 'block';
                        } else {
                            notificationBadge.style.display = 'none';
                        }
                    } else {
                        notificationsList.innerHTML = '<li><p class="dropdown-item text-muted text-center">No notifications</p></li>';
                        notificationBadge.style.display = 'none';
                    }
                } catch (error) {
                    console.error('Error fetching notifications:', error);
                }
            }
            fetchNotifications();
            setInterval(fetchNotifications, 60000); // Poll every 60 seconds
            {% endif %}
        });
    </script>
    {% block scripts %}{% endblock %}
</body>
</html>
"""

HOME_HTML = """
{% extends "layout.html" %}
{% block title %}Welcome{% endblock %}
{% block content %}
<div class="p-5 mb-4 rounded-3 card">
    <div class="container-fluid py-5">
        <h1 class="display-5 fw-bold" style="color: var(--dark-text);">Welcome to the Maternal Care Portal ✨</h1>
        <p class="col-md-8 fs-4">Your dedicated partner in the journey of motherhood. We provide comprehensive tools for both patients and doctors to ensure a healthy and happy pregnancy.</p>
        <a href="{{ url_for('login_chooser') }}" class="btn btn-primary btn-lg" type="button">Get Started</a>
    </div>
</div>

<div class="row align-items-md-stretch">
    <div class="col-md-6 mb-3">
        <div class="h-100 p-5 text-white rounded-3 card" style="background: linear-gradient(45deg, var(--primary-pink), #e83e8c) !important;">
            <h2>For Patients 🤰</h2>
            <p>Access your health records, connect with your doctor, and use our AI-powered tools for guidance and support. Your health, at your fingertips.</p>
            <a href="{{ url_for('login_patient') }}" class="btn btn-outline-light" type="button">Patient Login</a>
        </div>
    </div>
    <div class="col-md-6 mb-3">
        <div class="h-100 p-5 rounded-3 card">
            <h2>For Doctors 🩺</h2>
            <p>Manage your patients, view their progress, and provide timely care. A streamlined dashboard to help you make a difference.</p>
            <a href="{{ url_for('login_doctor') }}" class="btn btn-outline-secondary" type="button">Doctor Login</a>
        </div>
    </div>
</div>
{% endblock %}
"""

LOGIN_CHOOSER_HTML = """
{% extends "layout.html" %}
{% block title %}Select Login{% endblock %}
{% block content %}
<div class="text-center mt-5">
    <h1 class="mb-4">Login As 🤔</h1>
    <div class="d-grid gap-3 col-md-6 mx-auto">
        <a href="{{ url_for('login_patient') }}" class="btn btn-primary btn-lg p-4 shadow">
            <i class="bi bi-person-fill me-2"></i> I am a Patient
        </a>
        <a href="{{ url_for('login_doctor') }}" class="btn btn-secondary btn-lg p-4 shadow">
            <i class="bi bi-heart-pulse-fill me-2"></i> I am a Doctor
        </a>
    </div>
</div>
{% endblock %}
"""

LOGIN_PATIENT_HTML = """
{% extends "layout.html" %}
{% block title %}Patient Login{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-4">
        <div class="card">
            <div class="card-body p-4">
                <h3 class="card-title text-center mb-4">Patient Login 👩‍⚕️</h3>
                <form method="POST" action="{{ url_for('login_patient') }}">
                    <div class="mb-3">
                        <label for="email" class="form-label">Email address</label>
                        <input type="email" class="form-control" id="email" name="email" required value="jane.doe@example.com">
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required value="password123">
                    </div>
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">Login</button>
                    </div>
                </form>
                <div class="text-center mt-3">
                    <small>New patient? <a href="{{ url_for('register_patient') }}">Register here</a></small>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

LOGIN_DOCTOR_HTML = """
{% extends "layout.html" %}
{% block title %}Doctor Login{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-4">
        <div class="card">
            <div class="card-body p-4">
                <h3 class="card-title text-center mb-4">Doctor Login 🩺</h3>
                <form method="POST" action="{{ url_for('login_doctor') }}">
                    <div class="mb-3">
                        <label for="username" class="form-label">Username (Your Name)</label>
                        <input type="text" class="form-control" id="username" name="username" required value="Dr. Emily Carter">
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Password (Your Mobile Number)</label>
                        <input type="password" class="form-control" id="password" name="password" required value="5550001111">
                    </div>
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">Login</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

PATIENT_DASHBOARD_HTML = """
{% extends "layout.html" %}
{% block title %}Patient Dashboard{% endblock %}
{% block content %}
<h1 class="mb-4">Welcome, {{ patient.name }}!</h1>

<div class="row">
    <!-- Left Column -->
    <div class="col-lg-8">
        <!-- Emergency Contacts -->
        <div class="card text-white mb-4" style="background: linear-gradient(45deg, #dc3545, #b02a37) !important;">
            <div class="card-header fw-bold">🚨 EMERGENCY INFORMATION</div>
            <div class="card-body">
                <h5 class="card-title">Emergency Contact: {{ patient.emergency_contact_name }}</h5>
                <p class="card-text fs-4">{{ patient.emergency_contact_phone }}</p>
                <a href="tel:{{ patient.emergency_contact_phone }}" class="btn btn-light"><i class="bi bi-telephone-fill"></i> Call Contact</a>
                <a href="{{ url_for('patient_emergency') }}" class="btn btn-outline-light fw-bold float-end"><i class="bi bi-exclamation-triangle-fill"></i> Go to Emergency Page</a>
            </div>
        </div>

        <!-- Medical Info -->
        <div class="card mb-4">
            <div class="card-header">📄 Your Medical Information</div>
            <div class="card-body">
                <h5 class="card-title">Medical History</h5>
                <p class="card-text">{{ patient.medical_history|safe }}</p>
                <hr>
                <h5 class="card-title">Current Status</h5>
                <p class="card-text">{{ patient.current_status|safe }}</p>
            </div>
        </div>

        {% if recommended_articles %}
        <div class="card mb-4">
            <div class="card-header">💡 Recommended For You</div>
            <div class="list-group list-group-flush">
                {% for article in recommended_articles %}
                <a href="{{ url_for('view_article', article_id=article.id) }}" class="list-group-item list-group-item-action">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">{{ article.title }}</h6>
                        <span class="badge bg-info text-dark">{{ article.category }}</span>
                    </div>
                </a>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>

    <!-- Right Column -->
    <div class="col-lg-4">
        <!-- Assigned Doctor -->
        <div class="card mb-4">
            <div class="card-header">👨‍⚕️ Your Doctor</div>
            <div class="card-body">
                <h5 class="card-title">{{ patient.doctor.name }}</h5>
                <p class="card-text">{{ patient.doctor.specialty }}</p>
                <p class="card-text"><i class="bi bi-telephone-fill me-2"></i>{{ patient.doctor.mobile }}</p>
                <div class="d-grid gap-2">
                    <a href="tel:{{ patient.doctor.mobile }}" class="btn btn-outline-success"><i class="bi bi-telephone"></i> Call Doctor</a>
                    <a href="sms:{{ patient.doctor.mobile }}" class="btn btn-outline-primary"><i class="bi bi-chat-dots"></i> Message Doctor</a>
                </div>
            </div>
        </div>
        <!-- Quick Actions -->
        <div class="card">
            <div class="card-header">⚡ Quick Actions</div>
            <div class="list-group list-group-flush">
                <a href="{{ url_for('patient_consultant') }}" class="list-group-item list-group-item-action"><i class="bi bi-robot me-2"></i> AI Symptom Consultant</a>
                <a href="{{ url_for('patient_report_summary') }}" class="list-group-item list-group-item-action"><i class="bi bi-file-earmark-text me-2"></i> Summarize a Report</a>
                <a href="{{ url_for('patient_documents') }}" class="list-group-item list-group-item-action"><i class="bi bi-folder-symlink me-2"></i> My Documents</a>
                <a href="{{ url_for('patient_prescriptions') }}" class="list-group-item list-group-item-action"><i class="bi bi-prescription2 me-2"></i> My Prescriptions</a>
                <a href="{{ url_for('patient_appointments') }}" class="list-group-item list-group-item-action"><i class="bi bi-calendar-check me-2"></i> My Appointments</a>
                <a href="{{ url_for('messages') }}" class="list-group-item list-group-item-action"><i class="bi bi-chat-left-text me-2"></i> Messages</a>
                <a href="{{ url_for('resources') }}" class="list-group-item list-group-item-action"><i class="bi bi-book me-2"></i> Health Resources</a>
                <a href="{{ url_for('patient_wellness_log') }}" class="list-group-item list-group-item-action"><i class="bi bi-check2-circle me-2"></i> Daily Wellness Log</a>
            </div>
        </div>
    </div>
    <div class="col-12 mt-3">
        <form method="POST" action="{{ url_for('trigger_doula_checkin') }}">
            <button type="submit" class="btn btn-outline-secondary w-100">Trigger AI Doula Check-in (Manual Simulation)</button>
        </form>
    </div>
</div>
{% endblock %}
"""

PATIENT_CONSULTANT_HTML = """
{% extends "layout.html" %}
{% block title %}AI Consultant{% endblock %}
{% block content %}
<style>
    #chat-window { height: 60vh; overflow-y: auto; border: 1px solid var(--card-border-color); background-color: rgba(0,0,0,0.05); }
    .user-msg, .ai-msg { max-width: 80%; padding: 10px 15px; border-radius: 15px; margin-bottom: 10px; word-wrap: break-word; }
    .user-msg { background-color: var(--primary-pink); color: white; margin-left: auto; border-bottom-right-radius: 0; }
    .ai-msg { background-color: var(--glass-bg); border: 1px solid var(--card-border-color); margin-right: auto; border-bottom-left-radius: 0; }
</style>

<div class="card">
    <div class="card-header"><i class="bi bi-robot me-2"></i>AI Symptom Consultant 🤖</div>
    <div class="card-body">
        <div id="chat-window" class="p-3 rounded mb-3">
            <!-- Chat messages will appear here -->
        </div>
        <form id="chat-form">
            <div class="input-group">
                <input type="text" id="message-input" class="form-control" placeholder="Describe your symptoms..." required>
                <button class="btn btn-primary" type="submit" id="send-btn">
                    <i class="bi bi-send-fill"></i> Send
                </button>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatWindow = document.getElementById('chat-window');
    const sendBtn = document.getElementById('send-btn');
    let chatHistory = [];

    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const userInput = messageInput.value.trim();
        if (!userInput) return;

        addMessageToChat('user', userInput);
        messageInput.value = '';
        toggleLoading(true);

        try {
            const response = await fetch("{{ url_for('patient_consultant') }}", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userInput, history: chatHistory })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Network response was not ok');
            }

            const data = await response.json();
            addMessageToChat('ai', data.reply);
            
            chatHistory.push({ role: 'user', text: userInput });
            chatHistory.push({ role: 'model', text: data.reply });

        } catch (error) {
            addMessageToChat('ai', `Error: ${error.message}`);
        } finally {
            toggleLoading(false);
        }
    });

    function addMessageToChat(sender, message) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add(sender === 'user' ? 'user-msg' : 'ai-msg');
        
        if (sender === 'ai') {
            msgDiv.innerHTML = marked.parse(message);
        } else {
            msgDiv.textContent = message;
        }
        
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function toggleLoading(isLoading) {
        if (isLoading) {
            sendBtn.disabled = true;
            sendBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Thinking...`;
        } else {
            sendBtn.disabled = false;
            sendBtn.innerHTML = `<i class="bi bi-send-fill"></i> Send`;
        }
    }
});
</script>
{% endblock %}
"""

PATIENT_EMERGENCY_HTML = """
{% extends "layout.html" %}
{% block title %}Emergency Actions{% endblock %}
{% block content %}
<div class="text-center">
    <h1 class="display-4 text-danger fw-bold"><i class="bi bi-exclamation-triangle-fill"></i> EMERGENCY 🚨</h1>
    <p class="lead">Use these options only in a genuine emergency.</p>
</div>

<div class="card bg-danger-subtle border-danger my-4">
    <div class="card-body text-center">
        <h3 class="card-title">Immediate Actions</h3>
        <div class="d-grid gap-3 d-md-flex justify-content-md-center mt-4">
            <a href="tel:911" class="btn btn-danger btn-lg flex-grow-1"><i class="bi bi-telephone-outbound-fill me-2"></i>CALL AMBULANCE (911)</a>
            <a href="sms:{{ patient.emergency_contact_phone }}?&body=EMERGENCY! I need help. My location is [Please add your location]." class="btn btn-warning btn-lg flex-grow-1"><i class="bi bi-chat-text-fill me-2"></i>MESSAGE EMERGENCY CONTACT</a>
            <a href="sms:{{ patient.doctor.mobile }}?&body=EMERGENCY ALERT from your patient, {{ patient.name }}. Please contact me immediately." class="btn btn-info btn-lg text-white flex-grow-1"><i class="bi bi-bell-fill me-2"></i>NOTIFY DOCTOR</a>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header">
        <i class="bi bi-hospital-fill me-2"></i>Find Nearby Hospitals
    </div>
    <div class="card-body">
        <div class="mb-3">
            <button id="auto-find-btn" class="btn btn-primary"><i class="bi bi-geo-alt-fill me-2"></i>Find Hospitals Near Me</button>
        </div>
        <hr>
        <form id="manual-find-form">
            <label for="location-query" class="form-label">Or, search manually by city or address:</label>
            <div class="input-group">
                <input type="text" id="location-query" class="form-control" placeholder="e.g., 'New York, NY'">
                <button type="submit" class="btn btn-secondary">Search</button>
            </div>
        </form>
        <div id="hospital-results" class="mt-4">
            <!-- Results will be displayed here -->
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const autoFindBtn = document.getElementById('auto-find-btn');
    const manualFindForm = document.getElementById('manual-find-form');
    const locationQueryInput = document.getElementById('location-query');
    const resultsDiv = document.getElementById('hospital-results');

    autoFindBtn.addEventListener('click', () => {
        if (!navigator.geolocation) {
            showError('Geolocation is not supported by your browser.');
            return;
        }
        toggleLoading(autoFindBtn, true, 'Finding...');
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                findHospitals({ lat: latitude, lon: longitude });
                toggleLoading(autoFindBtn, false, '<i class="bi bi-geo-alt-fill me-2"></i>Find Hospitals Near Me');
            },
            () => {
                showError('Unable to retrieve your location. Please use the manual search.');
                toggleLoading(autoFindBtn, false, '<i class="bi bi-geo-alt-fill me-2"></i>Find Hospitals Near Me');
            }
        );
    });

    manualFindForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = locationQueryInput.value.trim();
        if (query) {
            findHospitals({ query: query });
        }
    });

    async function findHospitals(payload) {
        resultsDiv.innerHTML = `<div class="d-flex justify-content-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>`;
        try {
            const response = await fetch("{{ url_for('find_hospitals_api') }}", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            displayResults(data.facilities);
        } catch (error) {
            showError(error.message);
        }
    }

    function displayResults(facilities) {
        if (facilities.length === 0) {
            resultsDiv.innerHTML = '<div class="alert alert-warning">No medical facilities found for the specified location.</div>';
            return;
        }
        let html = '<ul class="list-group">';
        facilities.forEach(f => {
            html += `
                <li class="list-group-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">${f.name}</h5>
                        <small class="text-muted">${f.distance}</small>
                    </div>
                    <p class="mb-1">${f.address}</p>
                    <a href="https://www.google.com/maps/search/?api=1&query=${f.lat},${f.lon}" target="_blank" class="btn btn-sm btn-outline-primary">View on Map</a>
                </li>
            `;
        });
        html += '</ul>';
        resultsDiv.innerHTML = html;
    }

    function showError(message) {
        resultsDiv.innerHTML = `<div class="alert alert-danger">${message}</div>`;
    }

    function toggleLoading(button, isLoading, loadingText) {
        button.disabled = isLoading;
        if (isLoading) {
            button.innerHTML = `<span class="spinner-border spinner-border-sm"></span> ${loadingText}`;
        } else {
            button.innerHTML = loadingText;
        }
    }
});
</script>
{% endblock %}
"""

PATIENT_REPORT_SUMMARY_HTML = """
{% extends "layout.html" %}
{% block title %}Report Summarizer{% endblock %}
{% block content %}
<div class="card">
    <div class="card-header"><i class="bi bi-file-earmark-text-fill me-2"></i>AI Medical Report Summarizer 🔬</div>
    <div class="card-body">
        <p class="card-text">Upload a medical report (PNG, JPG, or PDF) to get a simplified summary of key findings.</p>
        <form id="report-form" enctype="multipart/form-data">
            <div class="mb-3">
                <label for="report-file" class="form-label">Select Report File</label>
                <input class="form-control" type="file" id="report-file" name="report_file" accept=".png,.jpg,.jpeg,.pdf" required>
            </div>
            <button type="submit" id="summarize-btn" class="btn btn-primary">
                <i class="bi bi-activity me-2"></i>Analyze and Summarize
            </button>
        </form>
        <div id="summary-results" class="mt-4" style="display: none;">
            <hr>
            <h3 class="mb-3">Analysis Summary</h3>
            <div id="loading-spinner" class="text-center" style="display: none;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p>Analyzing your report... this may take a moment.</p>
            </div>
            <div id="results-content"></div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const reportForm = document.getElementById('report-form');
    const summarizeBtn = document.getElementById('summarize-btn');
    const resultsDiv = document.getElementById('summary-results');
    const resultsContent = document.getElementById('results-content');
    const loadingSpinner = document.getElementById('loading-spinner');

    reportForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        if (!formData.get('report_file').name) {
            alert('Please select a file to upload.');
            return;
        }

        toggleLoading(true);

        try {
            const response = await fetch("{{ url_for('patient_report_summary') }}", {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }
            displaySummary(data);

        } catch (error) {
            displayError(error.message);
        } finally {
            toggleLoading(false);
        }
    });

    function displaySummary(data) {
        let html = `
            <div class="alert alert-success">
                <h4 class="alert-heading">🟢 Positive Findings</h4>
                <ul>${data.positives.length > 0 ? data.positives.map(item => `<li>${item}</li>`).join('') : '<li>No specific positive findings were extracted.</li>'}</ul>
            </div>
            <div class="alert alert-warning">
                <h4 class="alert-heading">🔴 Areas of Concern / Negative Findings</h4>
                <ul>${data.negatives.length > 0 ? data.negatives.map(item => `<li>${item}</li>`).join('') : '<li>No significant negative findings were extracted.</li>'}</ul>
            </div>
            <div class="alert alert-info mt-3">
                <strong>Disclaimer:</strong> This is an AI-generated summary and not a substitute for professional medical advice. Always discuss your report with your doctor.
            </div>
        `;
        resultsContent.innerHTML = html;
    }

    function displayError(message) {
        resultsContent.innerHTML = `<div class="alert alert-danger"><strong>Error:</strong> ${message}</div>`;
    }

    function toggleLoading(isLoading) {
        resultsDiv.style.display = 'block';
        summarizeBtn.disabled = isLoading;
        if (isLoading) {
            loadingSpinner.style.display = 'block';
            resultsContent.innerHTML = '';
            summarizeBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Analyzing...`;
        } else {
            loadingSpinner.style.display = 'none';
            summarizeBtn.innerHTML = `<i class="bi bi-activity me-2"></i>Analyze and Summarize`;
        }
    }
});
</script>
{% endblock %}
"""

DOCTOR_DASHBOARD_HTML = """
{% extends "layout.html" %}
{% block title %}Doctor Dashboard{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Your Patients 📋</h1>
    <a href="{{ url_for('doctor_add_patient') }}" class="btn btn-primary"><i class="bi bi-person-plus-fill me-2"></i>Add New Patient</a>
</div>

<div class="card mb-4">
    <div class="card-body">
        <form method="GET" action="{{ url_for('doctor_dashboard') }}">
            <div class="input-group">
                <input type="search" name="search" class="form-control" placeholder="Search for a patient by name..." value="{{ search_query or '' }}">
                <button class="btn btn-outline-secondary" type="submit"><i class="bi bi-search"></i></button>
            </div>
        </form>
    </div>
</div>

<div class="card">
    <div class="card-header">Patient Roster</div>
    {% if patients %}
    <div class="list-group list-group-flush">
        {% for patient in patients %}
        <a href="{{ url_for('doctor_view_patient', patient_id=patient.id) }}" class="list-group-item list-group-item-action">
            <div class="d-flex w-100 justify-content-between">
                <h5 class="mb-1">{{ patient.name }}</h5>
                <small>DOB: {{ patient.dob.strftime('%Y-%m-%d') }}</small>
            </div>
            <p class="mb-1">Email: {{ patient.email }} | Mobile: {{ patient.mobile }}</p>
        </a>
        {% endfor %}
    </div>
    {% else %}
    <div class="card-body">
        <p class="text-muted">
            {% if search_query %}
                No patients found matching your search criteria.
            {% else %}
                You have no patients assigned. Click 'Add New Patient' to get started.
            {% endif %}
        </p>
    </div>
    {% endif %}
</div>
{% endblock %}
"""

DOCTOR_VIEW_PATIENT_HTML = """
{% extends "layout.html" %}
{% block title %}View Patient{% endblock %}
{% block content %}
<a href="{{ url_for('doctor_dashboard') }}" class="btn btn-outline-secondary mb-3"><i class="bi bi-arrow-left"></i> Back to Dashboard</a>
<div class="card">
    <div class="card-header">
        <h3>Patient Details: {{ patient.name }} 👤</h3>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <h5><i class="bi bi-telephone-fill me-2"></i>Contact Information</h5>
                <ul class="list-unstyled">
                    <li><strong>Email:</strong> {{ patient.email }}</li>
                    <li><strong>Mobile:</strong> {{ patient.mobile }}</li>
                    <li><strong>Address:</strong> {{ patient.address or 'N/A' }}</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h5><i class="bi bi-person-badge me-2"></i>Emergency Contact</h5>
                <ul class="list-unstyled">
                    <li><strong>Name:</strong> {{ patient.emergency_contact_name or 'N/A' }}</li>
                    <li><strong>Phone:</strong> {{ patient.emergency_contact_phone or 'N/A' }}</li>
                    <!-- PRESCRIPTION_LINK_PLACEHOLDER -->
                </ul>
            </div>
        </div>
        <hr>
        <div class="row">
            <div class="col-md-6">
                <h5><i class="bi bi-droplet-fill me-2"></i>Additional Health Info</h5>
                <ul class="list-unstyled">
                    <li><strong>Blood Group:</strong> {{ patient.blood_group or 'N/A' }}</li>
                    <li><strong>Allergies:</strong> {{ patient.allergies or 'None reported' }}</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h5><i class="bi bi-journal-text me-2"></i>Pregnancy & Medication History</h5>
                <ul class="list-unstyled">
                    <li><strong>Current Medications:</strong> {{ patient.current_medications or 'None' }}</li>
                    <li><strong>Previous Pregnancies:</strong> {{ patient.previous_pregnancies or 'None reported' }}</li>
                </ul>
            </div>
        </div>
        <hr>
        <form method="POST" action="{{ url_for('doctor_edit_patient', patient_id=patient.id) }}">
            <div class="mb-3">
                <label for="medical_history" class="form-label"><h5>📜 Medical History</h5></label>
                <textarea class="form-control" id="medical_history" name="medical_history" rows="5">{{ patient.medical_history }}</textarea>
            </div>
            <div class="mb-3">
                <label for="current_status" class="form-label"><h5>✍️ Current Status & Notes</h5></label>
                <textarea class="form-control" id="current_status" name="current_status" rows="5">{{ patient.current_status }}</textarea>
            </div>
            <button type="submit" class="btn btn-primary"><i class="bi bi-save-fill me-2"></i>Save Changes</button>
        </form>
    </div>
</div>
{% endblock %}
"""

DOCTOR_ADD_PATIENT_HTML = """
{% extends "layout.html" %}
{% block title %}Add New Patient{% endblock %}
{% block content %}
<a href="{{ url_for('doctor_dashboard') }}" class="btn btn-outline-secondary mb-3"><i class="bi bi-arrow-left"></i> Back to Dashboard</a>
<div class="card">
    <div class="card-header">
        <h3>Add New Patient 🆕</h3>
    </div>
    <div class="card-body">
        <form method="POST" action="{{ url_for('doctor_add_patient') }}">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="name" class="form-label">Full Name</label>
                    <input type="text" class="form-control" id="name" name="name" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label for="email" class="form-label">Email Address</label>
                    <input type="email" class="form-control" id="email" name="email" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label for="password" class="form-label">Password (for patient login)</label>
                    <input type="password" class="form-control" id="password" name="password" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label for="mobile" class="form-label">Mobile Number</label>
                    <input type="tel" class="form-control" id="mobile" name="mobile" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label for="dob" class="form-label">Date of Birth</label>
                    <input type="date" class="form-control" id="dob" name="dob" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label for="due_date" class="form-label">Estimated Due Date</label>
                    <input type="date" class="form-control" id="due_date" name="due_date">
                </div>
                <div class="col-md-6 mb-3">
                    <label for="blood_group" class="form-label">Blood Group</label>
                    <input type="text" class="form-control" id="blood_group" name="blood_group" placeholder="e.g., O+">
                </div>
                <div class="col-12 mb-3">
                    <label for="allergies" class="form-label">Allergies</label>
                    <textarea class="form-control" id="allergies" name="allergies" rows="2" placeholder="e.g., Penicillin, Peanuts"></textarea>
                </div>
                <div class="col-12 mb-3">
                    <label for="current_medications" class="form-label">Current Medications</label>
                    <textarea class="form-control" id="current_medications" name="current_medications" rows="2" placeholder="e.g., Prenatal Vitamins, Iron Supplements"></textarea>
                </div>
                <div class="col-12 mb-3">
                    <label for="previous_pregnancies" class="form-label">Previous Pregnancy History</label>
                    <textarea class="form-control" id="previous_pregnancies" name="previous_pregnancies" rows="2" placeholder="e.g., 1 previous full-term pregnancy, no complications."></textarea>
                </div>
                 <div class="col-md-6 mb-3">
                    <label for="address" class="form-label">Address</label>
                    <input type="text" class="form-control" id="address" name="address">
                </div>
                <div class="col-md-6 mb-3">
                    <label for="emergency_contact_name" class="form-label">Emergency Contact Name</label>
                    <input type="text" class="form-control" id="emergency_contact_name" name="emergency_contact_name">
                </div>
                <div class="col-md-6 mb-3">
                    <label for="emergency_contact_phone" class="form-label">Emergency Contact Phone</label>
                    <input type="tel" class="form-control" id="emergency_contact_phone" name="emergency_contact_phone">
                </div>
            </div>
            <button type="submit" class="btn btn-primary"><i class="bi bi-person-plus-fill me-2"></i>Add Patient</button>
        </form>
    </div>
</div>
{% endblock %}
"""

PATIENT_WELLNESS_LOG_HTML = """
{% extends "layout.html" %}
{% block title %}Daily Wellness Log{% endblock %}
{% block content %}
<div class="card">
    <div class="card-header"><i class="bi bi-check2-circle me-2"></i>Daily Wellness Log 📝</div>
    <div class="card-body">
        <p>Log your daily readings here. This helps your doctor monitor your progress.</p>
        <form id="wellness-form">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="systolic" class="form-label">🩸 Blood Pressure (Systolic)</label>
                    <input type="number" class="form-control" id="systolic" placeholder="e.g., 120">
                </div>
                <div class="col-md-6 mb-3">
                    <label for="diastolic" class="form-label">🩸 Blood Pressure (Diastolic)</label>
                    <input type="number" class="form-control" id="diastolic" placeholder="e.g., 80">
                </div>
                <div class="col-md-6 mb-3">
                    <label for="water" class="form-label">💧 Water Intake (Liters)</label>
                    <input type="number" step="0.1" class="form-control" id="water" placeholder="e.g., 2.5">
                </div>
                <div class="col-md-6 mb-3">
                    <label for="mood" class="form-label">😊 Mood (1=Low, 5=Great)</label>
                    <input type="number" min="1" max="5" class="form-control" id="mood" placeholder="1-5">
                </div>
                <div class="col-12 mb-3">
                    <label for="symptoms" class="form-label">Any Other Symptoms (comma-separated)</label>
                    <input type="text" class="form-control" id="symptoms" placeholder="e.g., headache, mild swelling">
                </div>
            </div>
            <button type="submit" id="submit-log-btn" class="btn btn-primary">Submit Log</button>
        </form>

        <div id="log-results" class="mt-4" style="display:none;">
            <hr>
            <h4>Today's Summary & Feedback</h4>
            <div id="results-content"></div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('wellness-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const submitBtn = document.getElementById('submit-log-btn');
    const resultsDiv = document.getElementById('log-results');
    const resultsContent = document.getElementById('results-content');

    const data = {
        systolic: document.getElementById('systolic').value,
        diastolic: document.getElementById('diastolic').value,
        water: document.getElementById('water').value,
        mood: document.getElementById('mood').value,
        symptoms: document.getElementById('symptoms').value,
    };

    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Submitting...`;
    resultsDiv.style.display = 'block';
    resultsContent.innerHTML = '';

    try {
        const response = await fetch("{{ url_for('submit_wellness_log') }}", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const resultData = await response.json();

        if (resultData.error) {
            throw new Error(resultData.error);
        }

        let html = '<h5>Feedback:</h5><ul class="list-group">';
        resultData.alerts.forEach(alert => {
            if (alert) {
                let alertClass = 'list-group-item-info';
                if (alert.type === 'EMERGENCY') alertClass = 'list-group-item-danger';
                if (alert.type === 'DIET_WARNING') alertClass = 'list-group-item-warning';
                if (alert.type === 'POSITIVE_FEEDBACK') alertClass = 'list-group-item-success';
                html += `<li class="list-group-item ${alertClass}"><strong>${alert.title}:</strong> ${alert.message}</li>`;
            }
        });
        html += '</ul>';
        resultsContent.innerHTML = html;

    } catch (error) {
        resultsContent.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit Log';
    }
});
</script>
{% endblock %}
"""

REGISTER_PATIENT_HTML = """
{% extends "layout.html" %}
{% block title %}Patient Registration{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
        <div class="card shadow-sm">
            <div class="card-body p-4">
                <h3 class="card-title text-center mb-4">Create Your Patient Account ✨</h3>
                <form method="POST" action="{{ url_for('register_patient') }}">
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="name" class="form-label">Full Name</label>
                            <input type="text" class="form-control" id="name" name="name" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="email" class="form-label">Email Address</label>
                            <input type="email" class="form-control" id="email" name="email" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="password" class="form-label">Password</label>
                            <input type="password" class="form-control" id="password" name="password" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="mobile" class="form-label">Mobile Number</label>
                            <input type="tel" class="form-control" id="mobile" name="mobile" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="dob" class="form-label">Date of Birth</label>
                            <input type="date" class="form-control" id="dob" name="dob" required>
                        </div>
                <div class="col-md-6 mb-3">
                    <label for="due_date" class="form-label">Estimated Due Date (if known)</label>
                    <input type="date" class="form-control" id="due_date" name="due_date">
                </div>
                <div class="col-md-6 mb-3">
                    <label for="blood_group" class="form-label">Blood Group</label>
                    <input type="text" class="form-control" id="blood_group" name="blood_group" placeholder="e.g., A-">
                </div>
                <div class="col-12 mb-3">
                    <label for="allergies" class="form-label">Known Allergies</label>
                    <textarea class="form-control" id="allergies" name="allergies" rows="2" placeholder="e.g., Sulfa drugs, Aspirin"></textarea>
                </div>
                <div class="col-12 mb-3">
                    <label for="current_medications" class="form-label">Current Medications</label>
                    <textarea class="form-control" id="current_medications" name="current_medications" rows="2" placeholder="List any current medications..."></textarea>
                </div>
                <div class="col-12 mb-3">
                    <label for="previous_pregnancies" class="form-label">Previous Pregnancy History</label>
                    <textarea class="form-control" id="previous_pregnancies" name="previous_pregnancies" rows="2" placeholder="Note any previous pregnancies, outcomes, or complications..."></textarea>
                </div>
                         <div class="col-md-6 mb-3">
                            <label for="address" class="form-label">Address</label>
                            <input type="text" class="form-control" id="address" name="address">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="emergency_contact_name" class="form-label">Emergency Contact Name</label>
                            <input type="text" class="form-control" id="emergency_contact_name" name="emergency_contact_name">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="emergency_contact_phone" class="form-label">Emergency Contact Phone</label>
                            <input type="tel" class="form-control" id="emergency_contact_phone" name="emergency_contact_phone">
                        </div>
                    </div>
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">Register</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

PATIENT_PRESCRIPTIONS_HTML = """
{% extends "layout.html" %}
{% block title %}My Prescriptions{% endblock %}
{% block content %}
<h1 class="mb-4">My Prescriptions 💊</h1>
<div class="card">
    <div class="card-header">Current and Past Medications</div>
    {% if prescriptions %}
    <div class="list-group list-group-flush">
        {% for rx in prescriptions %}
        <div class="list-group-item">
            <h5 class="mb-1">{{ rx.medication }}</h5>
            <p class="mb-1"><strong>Dosage:</strong> {{ rx.dosage }} | <strong>Frequency:</strong> {{ rx.frequency }}</p>
            <p class="mb-1"><strong>Prescribed by:</strong> {{ rx.doctor.name }} on {{ rx.prescribed_date.strftime('%Y-%m-%d') }}</p>
            <small class="text-muted">Notes: {{ rx.notes or 'N/A' }}</small>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="card-body"><p class="text-muted">You have no prescriptions on record.</p></div>
    {% endif %}
</div>
{% endblock %}
"""

PATIENT_APPOINTMENTS_HTML = """
{% extends "layout.html" %}
{% block title %}My Appointments{% endblock %}
{% block content %}
<h1 class="mb-4">My Appointments 🗓️</h1>
<div class="row">
    <div class="col-md-7">
        <div class="card">
            <div class="card-header">Upcoming & Past Appointments</div>
            {% if appointments %}
            <div class="list-group list-group-flush">
                {% for appt in appointments %}
                <div class="list-group-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">Appointment with {{ appt.doctor.name }}</h5>
                        <span class="badge 
                            {% if appt.status == 'confirmed' %}bg-success
                            {% elif appt.status == 'pending' %}bg-warning text-dark
                            {% else %}bg-secondary{% endif %}
                        ">{{ appt.status|capitalize }}</span>
                    </div>
                    <p class="mb-1"><strong>Date & Time:</strong> {{ appt.appointment_time.strftime('%A, %B %d, %Y at %I:%M %p') }}</p>
                    <p class="mb-1"><strong>Reason:</strong> {{ appt.reason }}</p>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="card-body">
                <p class="text-muted">You have no appointments scheduled.</p>
            </div>
            {% endif %}
        </div>
    </div>
    <div class="col-md-5">
        <div class="card">
            <div class="card-header">Request a New Appointment</div>
            <div class="card-body">
                <form method="POST" action="{{ url_for('patient_appointments') }}">
                    <div class="mb-3">
                        <label for="appointment_time" class="form-label">Preferred Date and Time</label>
                        <input type="datetime-local" class="form-control" id="appointment_time" name="appointment_time" required>
                    </div>
                    <div class="mb-3">
                        <label for="reason" class="form-label">Reason for Visit</label>
                        <textarea class="form-control" id="reason" name="reason" rows="3" required placeholder="e.g., Routine check-up, feeling unwell..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Request Appointment</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

DOCTOR_APPOINTMENTS_HTML = """
{% extends "layout.html" %}
{% block title %}Manage Appointments{% endblock %}
{% block content %}
<h1 class="mb-4">Manage Appointments 🗓️</h1>
<div class="card">
    <div class="card-header">Appointment Requests & Schedule</div>
    {% if appointments %}
    <div class="list-group list-group-flush">
        {% for appt in appointments %}
        <div class="list-group-item">
            <div class="d-flex w-100 justify-content-between align-items-start">
                <div>
                    <h5 class="mb-1">Appointment with {{ appt.patient.name }}</h5>
                    <p class="mb-1"><strong>Date & Time:</strong> {{ appt.appointment_time.strftime('%A, %B %d, %Y at %I:%M %p') }}</p>
                    <p class="mb-1"><strong>Reason:</strong> {{ appt.reason }}</p>
                </div>
                <div>
                    {% if appt.status == 'pending' %}
                        <span class="badge bg-warning text-dark mb-2">Pending Confirmation</span>
                        <div class="btn-group" role="group">
                            <button onclick="updateAppointment({{ appt.id }}, 'confirm')" class="btn btn-sm btn-success">Confirm</button>
                            <button onclick="updateAppointment({{ appt.id }}, 'cancel')" class="btn btn-sm btn-danger">Cancel</button>
                        </div>
                    {% elif appt.status == 'confirmed' %}
                        <span class="badge bg-success">Confirmed</span>
                    {% else %}
                        <span class="badge bg-secondary">Cancelled</span>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="card-body">
        <p class="text-muted">You have no appointments scheduled.</p>
    </div>
    {% endif %}
</div>
{% endblock %}
{% block scripts %}
<script>
async function updateAppointment(id, action) {
    try {
        const response = await fetch(`/api/appointments/${action}/${id}`, { method: 'POST' });
        if (response.ok) {
            window.location.reload();
        } else {
            const data = await response.json();
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('An error occurred: ' + error);
    }
}
</script>
{% endblock %}
"""

RESOURCES_HTML = """
{% extends "layout.html" %}
{% block title %}Health Resources{% endblock %}
{% block content %}
<h1 class="mb-4">Health Resources Library 📚</h1>
<p>A collection of articles to guide you through your pregnancy journey.</p>
<div class="row">
    {% for article in articles %}
    <div class="col-md-6 col-lg-4 mb-4">
        <div class="card h-100">
            <div class="card-body d-flex flex-column">
                <h5 class="card-title">{{ article.title }}</h5>
                <p class="card-text"><span class="badge bg-primary">{{ article.category }}</span></p>
                <p class="card-text">{{ article.content[:100] }}...</p>
                <a href="{{ url_for('view_article', article_id=article.id) }}" class="btn btn-outline-primary mt-auto">Read More</a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
"""

ARTICLE_VIEW_HTML = """
{% extends "layout.html" %}
{% block title %}{{ article.title }}{% endblock %}
{% block content %}
<a href="{{ url_for('resources') }}" class="btn btn-outline-secondary mb-3"><i class="bi bi-arrow-left"></i> Back to Resources</a>
<div class="card">
    <div class="card-body">
        <h1 class="card-title">{{ article.title }}</h1>
        <p class="text-muted">Category: <span class="badge bg-primary">{{ article.category }}</span> | Published: {{ article.publish_date.strftime('%B %d, %Y') }}</p>
        <hr>
        <div class="article-content">
            {{ article.content|safe }}
        </div>
    </div>
</div>
{% endblock %}
"""

MESSAGES_HTML = """
{% extends "layout.html" %}
{% block title %}Messages{% endblock %}
{% block content %}
<h1 class="mb-4">Your Conversations 💬</h1>
<div class="card">
    <div class="card-header">Message Center</div>
    {% if conversations %}
    <div class="list-group list-group-flush">
        {% for user, last_message in conversations.items() %}
        <a href="{{ url_for('conversation', user_type=user.get_id().split('-')[0], user_id=user.id) }}" class="list-group-item list-group-item-action">
            <div class="d-flex w-100 justify-content-between">
                <h5 class="mb-1">Conversation with {{ user.name }}</h5>
                <small>{{ last_message.timestamp.strftime('%Y-%m-%d %H:%M') }}</small>
            </div>
            <p class="mb-1 text-muted">{{ last_message.content[:80] }}{% if last_message.content|length > 80 %}...{% endif %}</p>
        </a>
        {% endfor %}
    </div>
    {% else %}
    <div class="card-body">
        <p class="text-muted">You have no conversations yet.</p>
    </div>
    {% endif %}
</div>
{% endblock %}
"""

CONVERSATION_HTML = """
{% extends "layout.html" %}
{% block title %}Conversation with {{ other_user.name }}{% endblock %}
{% block content %}
<style>
    #chat-window { height: 60vh; overflow-y: auto; border: 1px solid var(--card-border-color); background-color: rgba(0,0,0,0.05); }
    .user-msg, .other-msg { max-width: 80%; padding: 10px 15px; border-radius: 15px; margin-bottom: 10px; word-wrap: break-word; }
    .user-msg { background-color: var(--primary-pink); color: white; margin-left: auto; border-bottom-right-radius: 0; }
    .other-msg { background-color: var(--glass-bg); border: 1px solid var(--card-border-color); margin-right: auto; border-bottom-left-radius: 0; }
</style>
<a href="{{ url_for('messages') }}" class="btn btn-outline-secondary mb-3"><i class="bi bi-arrow-left"></i> Back to Conversations</a>
<div class="card">
    <div class="card-header">Conversation with {{ other_user.name }}</div>
    <div class="card-body">
        <div id="chat-window" class="p-3 rounded mb-3">
            {% for message in messages %}
                <div class="{{ 'user-msg' if message.sender_id == current_user.id and message.sender_type == session.user_type else 'other-msg' }}">
                    {{ message.content }}
                </div>
            {% endfor %}
        </div>
        <form method="POST">
            <div class="input-group">
                <input type="text" name="content" class="form-control" placeholder="Type your message..." required>
                <button class="btn btn-primary" type="submit"><i class="bi bi-send-fill"></i> Send</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
"""

DOCTOR_PRESCRIPTIONS_HTML = """
{% extends "layout.html" %}
{% block title %}Prescriptions for {{ patient.name }}{% endblock %}
{% block content %}
<a href="{{ url_for('doctor_view_patient', patient_id=patient.id) }}" class="btn btn-outline-secondary mb-3"><i class="bi bi-arrow-left"></i> Back to Patient</a>
<h1 class="mb-4">Prescriptions for {{ patient.name }} 💊</h1>
<div class="row">
    <div class="col-md-7">
        <div class="card">
            <div class="card-header">Prescription History</div>
            {% if prescriptions %}
            <div class="list-group list-group-flush">
                {% for rx in prescriptions %}
                <div class="list-group-item">
                    <h5 class="mb-1">{{ rx.medication }}</h5>
                    <p class="mb-1"><strong>Dosage:</strong> {{ rx.dosage }} | <strong>Frequency:</strong> {{ rx.frequency }}</p>
                    <small class="text-muted">Prescribed on {{ rx.prescribed_date.strftime('%Y-%m-%d') }}. Notes: {{ rx.notes or 'N/A' }}</small>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="card-body"><p class="text-muted">No prescriptions on record for this patient.</p></div>
            {% endif %}
        </div>
    </div>
    <div class="col-md-5">
        <div class="card">
            <div class="card-header">Add New Prescription</div>
            <div class="card-body">
                <form method="POST" action="{{ url_for('doctor_add_prescription', patient_id=patient.id) }}">
                    <div class="mb-3"><label for="medication" class="form-label">Medication Name</label><input type="text" class="form-control" name="medication" required></div>
                    <div class="mb-3"><label for="dosage" class="form-label">Dosage (e.g., 500mg)</label><input type="text" class="form-control" name="dosage" required></div>
                    <div class="mb-3"><label for="frequency" class="form-label">Frequency (e.g., Twice a day)</label><input type="text" class="form-control" name="frequency" required></div>
                    <div class="mb-3"><label for="notes" class="form-label">Notes</label><textarea class="form-control" name="notes" rows="2"></textarea></div>
                    <button type="submit" class="btn btn-primary">Add Prescription</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

PATIENT_DOCUMENTS_HTML = """
{% extends "layout.html" %}
{% block title %}My Documents{% endblock %}
{% block content %}
<h1 class="mb-4">My Documents 📂</h1>
<div class="row">
    <div class="col-md-7">
        <div class="card">
            <div class="card-header">Uploaded Documents</div>
            {% if documents %}
            <div class="list-group list-group-flush">
                {% for doc in documents %}
                <div class="list-group-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1"><i class="bi bi-file-earmark-text me-2"></i>{{ doc.file_name }}</h5>
                        <a href="{{ url_for('view_document', doc_id=doc.id) }}" target="_blank" class="btn btn-sm btn-outline-primary">View/Download</a>
                    </div>
                    <p class="mb-1">{{ doc.description }}</p>
                    <small class="text-muted">Uploaded on: {{ doc.upload_date.strftime('%Y-%m-%d') }}</small>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="card-body"><p class="text-muted">You have not uploaded any documents.</p></div>
            {% endif %}
        </div>
    </div>
    <div class="col-md-5">
        <div class="card">
            <div class="card-header">Upload New Document</div>
            <div class="card-body">
                <p class="small text-muted">Note: For demonstration, files are stored in the database. In a production app, a cloud storage service would be used.</p>
                <form method="POST" enctype="multipart/form-data">
                    <div class="mb-3">
                        <label for="file" class="form-label">Select File</label>
                        <input type="file" class="form-control" name="file" required>
                    </div>
                    <div class="mb-3">
                        <label for="description" class="form-label">Description</label>
                        <input type="text" class="form-control" name="description" placeholder="e.g., 'Lab Results from June'" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Upload Document</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

DOCTOR_PATIENT_DOCUMENTS_HTML = """
{% extends "layout.html" %}
{% block title %}Documents for {{ patient.name }}{% endblock %}
{% block content %}
<a href="{{ url_for('doctor_view_patient', patient_id=patient.id) }}" class="btn btn-outline-secondary mb-3"><i class="bi bi-arrow-left"></i> Back to Patient Details</a>
<h1 class="mb-4">Documents for {{ patient.name }} 📂</h1>
<div class="card">
    <div class="card-header">Uploaded Documents</div>
    {% if documents %}
    <div class="list-group list-group-flush">
        {% for doc in documents %}
        <div class="list-group-item">
            <div class="d-flex w-100 justify-content-between">
                <h5 class="mb-1"><i class="bi bi-file-earmark-text me-2"></i>{{ doc.file_name }}</h5>
                <a href="{{ url_for('view_document', doc_id=doc.id) }}" target="_blank" class="btn btn-sm btn-outline-primary">View/Download</a>
            </div>
            <p class="mb-1">{{ doc.description }}</p>
            <small class="text-muted">Uploaded on: {{ doc.upload_date.strftime('%Y-%m-%d') }}</small>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="card-body"><p class="text-muted">This patient has not uploaded any documents.</p></div>
    {% endif %}
</div>
{% endblock %}
"""

DIGITAL_DOULA_HTML = """
{% extends "layout.html" %}
{% block title %}Digital Doula{% endblock %}
{% block content %}
<style>
    #chat-window { height: 60vh; overflow-y: auto; border: 1px solid var(--card-border-color); background-color: rgba(0,0,0,0.05); }
    .user-msg, .ai-msg { max-width: 80%; padding: 10px 15px; border-radius: 15px; margin-bottom: 10px; word-wrap: break-word; }
    .user-msg { background-color: var(--primary-pink); color: white; margin-left: auto; border-bottom-right-radius: 0; }
    .ai-msg { background-color: var(--glass-bg); border: 1px solid var(--card-border-color); margin-right: auto; border-bottom-left-radius: 0; }
</style>
<div class="card">
    <div class="card-header">AI Digital Doula & Postpartum Companion 🤖💖</div>
    <div class="card-body">
        <div id="chat-window" class="p-3 rounded mb-3">
            {% for log in chat_logs %}
                <div class="{{ 'user-msg' if log.message_from == 'patient' else 'ai-msg' }}">
                    {{ log.content|safe }}
                </div>
            {% endfor %}
        </div>
        <form method="POST">
            <div class="input-group">
                <input type="text" name="content" class="form-control" placeholder="Ask a question or respond..." required autofocus>
                <button class="btn btn-primary" type="submit"><i class="bi bi-send-fill"></i> Send</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
"""

# ==============================================================================
# 1a. JINJA2 TEMPLATE SETUP
# ==============================================================================

class DictLoader(BaseLoader):
    """A Jinja2 loader that loads templates from a dictionary."""
    def __init__(self, templates):
        self.templates = templates

    def get_source(self, environment, template):
        if template in self.templates:
            source = self.templates[template]
            # No path, mtime, and uptodate function needed for string templates
            return source, None, lambda: True
        raise TemplateNotFound(template)

TEMPLATES = {
    'layout.html': LAYOUT_HTML,
    'home.html': HOME_HTML,
    'login_chooser.html': LOGIN_CHOOSER_HTML,
    'login_patient.html': LOGIN_PATIENT_HTML,
    'login_doctor.html': LOGIN_DOCTOR_HTML,
    'patient_dashboard.html': PATIENT_DASHBOARD_HTML,
    'patient_consultant.html': PATIENT_CONSULTANT_HTML,
    'patient_emergency.html': PATIENT_EMERGENCY_HTML,
    'patient_report_summary.html': PATIENT_REPORT_SUMMARY_HTML,
    'doctor_dashboard.html': DOCTOR_DASHBOARD_HTML,
    'doctor_view_patient.html': DOCTOR_VIEW_PATIENT_HTML,
    'doctor_add_patient.html': DOCTOR_ADD_PATIENT_HTML,
    'patient_wellness_log.html': PATIENT_WELLNESS_LOG_HTML,
    'register_patient.html': REGISTER_PATIENT_HTML,
    'patient_prescriptions.html': PATIENT_PRESCRIPTIONS_HTML,
    'patient_documents.html': PATIENT_DOCUMENTS_HTML,
    'digital_doula.html': DIGITAL_DOULA_HTML,
    'doctor_prescriptions.html': DOCTOR_PRESCRIPTIONS_HTML,
    'patient_appointments.html': PATIENT_APPOINTMENTS_HTML,
    'doctor_appointments.html': DOCTOR_APPOINTMENTS_HTML,
    'resources.html': RESOURCES_HTML,
    'article_view.html': ARTICLE_VIEW_HTML,
    'messages.html': MESSAGES_HTML,
    'conversation.html': CONVERSATION_HTML,
    'doctor_patient_documents.html': DOCTOR_PATIENT_DOCUMENTS_HTML,
}

# ==============================================================================
# 2. INITIAL CONFIGURATION & SETUP
# ==============================================================================

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_for_maternal_health_app'
# --- Use the provided PostgreSQL Database URL ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_Z1XQUFT0YhBI@ep-delicate-mountain-adckue32-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Custom Jinja2 Loader ---
app.jinja_loader = DictLoader(TEMPLATES)

# --- Database and Login Manager ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_chooser'
login_manager.login_message_category = 'info'

# --- Gemini API Configuration ---
API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


class Doctor(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    specialty = db.Column(db.String(100), default="Obstetrics & Gynecology")
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    patients = db.relationship('Patient', backref='doctor', lazy=True)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_id(self):
        return f"doctor-{self.id}"

class Patient(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200))
    dob = db.Column(db.Date)
    due_date = db.Column(db.Date)
    medical_history = db.Column(db.Text, default="No significant medical history.")
    blood_group = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    previous_pregnancies = db.Column(db.Text)
    current_status = db.Column(db.Text, default="Stable. Routine check-ups ongoing.")
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_id(self):
        return f"patient-{self.id}"

class WellnessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    log_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    systolic = db.Column(db.Integer)
    diastolic = db.Column(db.Integer)
    water_liters = db.Column(db.Float)
    mood = db.Column(db.Integer)
    symptoms = db.Column(db.Text)
    overall_status = db.Column(db.String(10)) # GREEN, ORANGE, RED

    patient = db.relationship('Patient', backref=db.backref('wellness_logs', lazy=True))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointment_time = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') # pending, confirmed, cancelled

    patient = db.relationship('Patient', backref=db.backref('appointments', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('appointments', lazy=True))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    publish_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    sender_type = db.Column(db.String(20), nullable=False) # 'patient' or 'doctor'
    receiver_id = db.Column(db.Integer, nullable=False)
    receiver_type = db.Column(db.String(20), nullable=False) # 'patient' or 'doctor'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_sender(self):
        return Doctor.query.get(self.sender_id) if self.sender_type == 'doctor' else Patient.query.get(self.sender_id)

    def get_receiver(self):
        return Doctor.query.get(self.receiver_id) if self.receiver_type == 'doctor' else Patient.query.get(self.receiver_id)

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    medication = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    prescribed_date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.Text)

    patient = db.relationship('Patient', backref=db.backref('prescriptions', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('prescriptions', lazy=True))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link_url = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    file_data = db.Column(db.LargeBinary, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref=db.backref('documents', lazy=True))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class DigitalDoulaLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_from = db.Column(db.String(10), nullable=False) # 'ai' or 'patient'
    content = db.Column(db.Text, nullable=False)

    patient = db.relationship('Patient', backref=db.backref('doula_logs', lazy=True))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
# ==============================================================================
# 4. USER SESSION MANAGEMENT (Flask-Login)
# ==============================================================================

@login_manager.user_loader
def load_user(user_id):
    try:
        user_type, user_actual_id = user_id.split('-')
        if user_type == 'doctor':
            return Doctor.query.get(int(user_actual_id))
        elif user_type == 'patient':
            return Patient.query.get(int(user_actual_id))
    except (ValueError, TypeError):
        return None
    return None

# ==============================================================================
# 5. CORE WEBSITE ROUTES (Login, Logout, Home)
# ==============================================================================

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login_chooser():
    return render_template('login_chooser.html')

@app.route('/login/patient', methods=['GET', 'POST'])
def login_patient():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        patient = Patient.query.filter_by(email=email).first()

        if patient and check_password_hash(patient.password_hash, password):
            login_user(patient)
            session['user_type'] = 'patient'
            flash('Login successful!', 'success')
            return redirect(url_for('patient_dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    return render_template('login_patient.html')

@app.route('/login/doctor', methods=['GET', 'POST'])
def login_doctor():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        doctor = Doctor.query.filter_by(name=username).first()

        if doctor and doctor.mobile == password:
            login_user(doctor)
            session['user_type'] = 'doctor'
            flash(f'Welcome back, {doctor.name}!', 'success')
            return redirect(url_for('doctor_dashboard'))
        else:
            flash('Invalid username or mobile number. Please try again.', 'danger')
    return render_template('login_doctor.html')

@app.route('/register/patient', methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        form_data = request.form
        name = form_data.get('name')
        email = form_data.get('email')
        password = form_data.get('password')

        if not all([name, email, password]):
            flash('Full Name, Email, and Password are required.', 'danger')
            return render_template('register_patient.html')

        if Patient.query.filter_by(email=email).first():
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('login_patient'))

        # Assign a doctor. For now, we'll assign the first available doctor.
        # In a real-world app, this logic would be more complex.
        doctor = Doctor.query.first()
        if not doctor:
            flash('No doctors are available for assignment. Please contact support.', 'danger')
            return render_template('register_patient.html')

        try:
            new_patient = Patient(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                mobile=form_data.get('mobile'),
                dob=datetime.strptime(form_data.get('dob'), '%Y-%m-%d').date() if form_data.get('dob') else None,
                due_date=datetime.strptime(form_data.get('due_date'), '%Y-%m-%d').date() if form_data.get('due_date') else None,
                blood_group=form_data.get('blood_group'),
                allergies=form_data.get('allergies'),
                current_medications=form_data.get('current_medications'),
                previous_pregnancies=form_data.get('previous_pregnancies'),
                address=form_data.get('address'),
                emergency_contact_name=form_data.get('emergency_contact_name'),
                emergency_contact_phone=form_data.get('emergency_contact_phone'),
                doctor_id=doctor.id
            )
            db.session.add(new_patient)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login_patient'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {e}', 'danger')

    return render_template('register_patient.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('home'))

# ==============================================================================
# 6. PATIENT PORTAL ROUTES
# ==============================================================================

@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if session.get('user_type') != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    # Personalized content logic
    recommended_articles = []
    if current_user.due_date:
        weeks_pregnant = (40 - (current_user.due_date - datetime.utcnow().date()).days / 7)
        trimester = 0
        if weeks_pregnant <= 13:
            trimester = 1
            recommended_articles = Article.query.filter(Article.category.ilike('%First Trimester%')).limit(2).all()
        elif 14 <= weeks_pregnant <= 27:
            trimester = 2
            recommended_articles = Article.query.filter(Article.category.ilike('%Second Trimester%')).limit(2).all()
        else:
            trimester = 3
            recommended_articles = Article.query.filter(Article.category.ilike('%Third Trimester%')).limit(2).all()
    
    # Add a general article if no specific ones are found
    if not recommended_articles:
        recommended_articles = Article.query.filter(Article.category == 'Nutrition').limit(1).all()

    return render_template('patient_dashboard.html', patient=current_user, recommended_articles=recommended_articles)

@app.route('/patient/appointments', methods=['GET', 'POST'])
@login_required
def patient_appointments():
    if session.get('user_type') != 'patient': return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            appointment_time_str = request.form.get('appointment_time')
            appointment_time = datetime.strptime(appointment_time_str, '%Y-%m-%dT%H:%M')
            reason = request.form.get('reason')
            
            new_appt = Appointment(
                patient_id=current_user.id,
                doctor_id=current_user.doctor_id,
                appointment_time=appointment_time,
                reason=reason,
                status='pending'
            )
            db.session.add(new_appt)
            db.session.commit()

            # Create notification for doctor
            notification = Notification(
                user_id=current_user.doctor_id, user_type='doctor',
                message=f'New appointment request from {current_user.name}.',
                link_url=url_for('doctor_appointments')
            )
            db.session.add(notification)
            db.session.commit()
            flash('Appointment requested successfully. You will be notified upon confirmation.', 'success')
        except Exception as e:
            flash(f'Error requesting appointment: {e}', 'danger')
        return redirect(url_for('patient_appointments'))

    appointments = Appointment.query.filter_by(patient_id=current_user.id).order_by(Appointment.appointment_time.desc()).all()
    return render_template('patient_appointments.html', appointments=appointments)

@app.route('/patient/prescriptions')
@login_required
def patient_prescriptions():
    if session.get('user_type') != 'patient': return redirect(url_for('home'))
    prescriptions = Prescription.query.filter_by(patient_id=current_user.id).order_by(Prescription.prescribed_date.desc()).all()
    return render_template('patient_prescriptions.html', prescriptions=prescriptions)

@app.route('/patient/documents', methods=['GET', 'POST'])
@login_required
def patient_documents():
    if session.get('user_type') != 'patient': return redirect(url_for('home'))
    
    if request.method == 'POST':
        file = request.files.get('file')
        description = request.form.get('description')
        if file and file.filename != '':
            new_doc = Document(
                patient_id=current_user.id,
                file_name=file.filename,
                description=description,
                file_data=file.read(),
                mime_type=file.mimetype
            )
            db.session.add(new_doc)
            db.session.commit()
            flash('Document uploaded successfully.', 'success')
            return redirect(url_for('patient_documents'))
    documents = Document.query.filter_by(patient_id=current_user.id).order_by(Document.upload_date.desc()).all()
    return render_template('patient_documents.html', documents=documents)

AI_CONSULTANT_SYSTEM_PROMPT = """
You are a preliminary symptom analysis AI for maternal health. Your function is to analyze the user's symptoms, 
suggest potential, common, and related conditions for informational purposes, and offer general advice.
CRITICAL SAFETY INSTRUCTION: You MUST start every response with a prominent safety disclaimer.
The disclaimer must be: "🚨 **Safety Warning:** I am an AI, not a medical professional. The information provided is for informational purposes only and is NOT medical advice. Always seek immediate consultation with a qualified doctor or emergency services for any medical concerns."
After the disclaimer, provide a structured response that includes:
1.  **Suggested Potential Conditions:** (1-3 brief points).
2.  **Recommended Next Steps:** (always include consulting a doctor, and other relevant advice like rest, hydration, monitoring, etc.).
Keep your response empathetic, clear, and formatted with Markdown for better readability.
And finnaly give the best food tips and best food advices to their pain in very clear and basic english""" 

@app.route('/patient/consultant', methods=['GET', 'POST'])
@login_required
def patient_consultant():
    if session.get('user_type') != 'patient':
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        user_input = request.json.get('message')
        chat_history = request.json.get('history', [])

        if not user_input:
            return jsonify({'error': 'Empty message received.'}), 400

        # Append the new user message to the history for the API call
        chat_history.append({'role': 'user', 'text': user_input})

        # Prepare payload for the requests-based API call
        contents = [
            {"role": "user" if msg['role'] == 'user' else 'model', "parts": [{"text": msg['text']}]}
            for msg in chat_history
        ]
        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": AI_CONSULTANT_SYSTEM_PROMPT}]},
        }
        headers = {'Content-Type': 'application/json'}
        url_with_key = f"{GEMINI_API_URL}?key={API_KEY}"
        
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(url_with_key, headers=headers, data=json.dumps(payload))
                response.raise_for_status()

                result = response.json()
                model_response_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')

                if model_response_text:
                    return jsonify({'reply': model_response_text})
                else:
                    # This will be caught by the final error message if all retries fail
                    raise ValueError("Model returned an empty or malformed response.")

            except (requests.exceptions.RequestException, KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return jsonify({'error': "Connection Error: Failed to get a valid response from the AI after multiple retries."}), 500

    return render_template('patient_consultant.html')

@app.route('/patient/emergency')
@login_required
def patient_emergency():
    if session.get('user_type') != 'patient':
        return redirect(url_for('home'))
    return render_template('patient_emergency.html', patient=current_user)

@app.route('/api/find_hospitals', methods=['POST'])
@login_required
def find_hospitals_api():
    """
    Finds nearby hospitals using the Overpass API instead of osmnx to reduce package size.
    """
    data = request.get_json()
    location_query = data.get('query')
    lat = data.get('lat')
    lon = data.get('lon')

    
    if not location_query and not (lat and lon):
        return jsonify({'error': 'Location query or coordinates are required.'}), 400
    
    try:
        # Step 1: Geocode if only a query is provided
        if not (lat and lon):
            nominatim_url = f"https://nominatim.openstreetmap.org/search?q={location_query}&format=json&limit=1"
            headers = {'User-Agent': 'MaternalCareApp/1.0'}
            geo_response = requests.get(nominatim_url, headers=headers)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            if not geo_data:
                return jsonify({'error': f"Could not find coordinates for '{location_query}'."}), 404
            lat = float(geo_data[0]['lat'])
            lon = float(geo_data[0]['lon'])

        # Step 2: Query Overpass API for hospitals
        overpass_url = "https://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json];
        (
          node["amenity"~"hospital|clinic|doctors"]["healthcare"="hospital"](around:10000,{lat},{lon});
          way["amenity"~"hospital|clinic|doctors"]["healthcare"="hospital"](around:10000,{lat},{lon});
          relation["amenity"~"hospital|clinic|doctors"]["healthcare"="hospital"](around:10000,{lat},{lon});
        );
        out center;
        """
        response = requests.post(overpass_url, data=overpass_query)
        response.raise_for_status()
        data = response.json()

        if not data.get('elements'):
            return jsonify({'facilities': []})

        # Step 3: Process and sort results
        results = []
        for element in data['elements']:
            tags = element.get('tags', {})
            name = tags.get('name', 'Unnamed Facility')
            addr = f"{tags.get('addr:housenumber', '')} {tags.get('addr:street', '')}".strip()
            elem_lat = element.get('center', {}).get('lat', element.get('lat'))
            elem_lon = element.get('center', {}).get('lon', element.get('lon'))
            distance = geodesic((lat, lon), (elem_lat, elem_lon)).km
            results.append({'name': name, 'address': addr or 'Address not available', 'distance': f"{distance:.2f} km", 'lat': elem_lat, 'lon': elem_lon})
        
        results.sort(key=lambda x: float(x['distance'].split(' ')[0]))
        results = results[:10]

        return jsonify({'facilities': results})
    except Exception as e:
        return jsonify({'error': f"An error occurred while finding facilities: {e}"}), 500

@app.route('/patient/report_summary', methods=['GET', 'POST'])
@login_required
def patient_report_summary():
    if session.get('user_type') != 'patient':
        return redirect(url_for('home'))

    if request.method == 'POST':
        file = request.files.get('report_file')
        if not file:
            return jsonify({'error': 'No file uploaded.'}), 400

        try:
            encoded_string = base64.b64encode(file.read()).decode('utf-8')
            mime_type = file.mimetype
    
            if mime_type not in ['image/png', 'image/jpeg', 'image/webp', 'application/pdf']:
                 return jsonify({'error': 'Unsupported file type. Please use PNG, JPEG, or PDF.'}), 400

            # Define the prompt and payload
            system_prompt = "You are a professional medical report summarizer. Analyze the provided report (image or PDF). Extract key findings and categorize them strictly into 'positives' (good news) and 'negatives' (areas of concern). Provide the response as a JSON object."
            user_query = "Please analyze this medical report and provide the summary structured into positives and negatives."
            payload = {
                "contents": [{"role": "user", "parts": [{"text": user_query}, {"inlineData": {"mimeType": mime_type, "data": encoded_string}}]}],
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": {
                        "type": "OBJECT",
                        "properties": {"positives": {"type": "ARRAY", "items": {"type": "STRING"}}, "negatives": {"type": "ARRAY", "items": {"type": "STRING"}}},
                        "required": ["positives", "negatives"]
                     }
                }
            }
    
            headers = {'Content-Type': 'application/json'}
            url_with_key = f"{GEMINI_API_URL}?key={API_KEY}"
            api_response = requests.post(url_with_key, headers=headers, data=json.dumps(payload))
            api_response.raise_for_status()
            json_text = api_response.json()['candidates'][0]['content']['parts'][0]['text']
            return jsonify(json.loads(json_text))
        except Exception as e:
            return jsonify({'error': f'An error occurred during analysis: {str(e)}'}), 500

    return render_template('patient_report_summary.html')

@app.route('/patient/wellness_log')
@login_required
def patient_wellness_log():
    if session.get('user_type') != 'patient':
        return redirect(url_for('home'))
    return render_template('patient_wellness_log.html')

@app.route('/api/wellness_log', methods=['POST'], endpoint='submit_wellness_log')
@login_required
def submit_wellness_log():
    if session.get('user_type') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    
    # --- Integrate PregnancyMonitor Logic ---
    BP_HIGH_EMERGENCY = (140, 90)
    BP_HIGH_WARNING = (130, 80)
    BP_LOW_WARNING = (90, 60)
    MIN_WATER_INTAKE_LITERS = 2.0
    MOOD_LOW_THRESHOLD = 2

    alerts = []
    
    systolic = int(data.get('systolic')) if data.get('systolic') else None
    diastolic = int(data.get('diastolic')) if data.get('diastolic') else None
    water = float(data.get('water')) if data.get('water') else None
    mood = int(data.get('mood')) if data.get('mood') else None
    symptoms_str = data.get('symptoms', '')

    # Blood Pressure Analysis
    if systolic and diastolic:
        if systolic >= BP_HIGH_EMERGENCY[0] or diastolic >= BP_HIGH_EMERGENCY[1]:
            alerts.append({ "type": "EMERGENCY", "title": "High Blood Pressure Alert!", "message": f"Reading of {systolic}/{diastolic} mmHg is in a critical range. Contact your doctor immediately.", "action": "SEND_SMS" })
        elif systolic >= BP_HIGH_WARNING[0] or diastolic >= BP_HIGH_WARNING[1]:
            alerts.append({ "type": "DIET_WARNING", "title": "Elevated Blood Pressure", "message": "Your BP is elevated. Monitor it closely and focus on low-sodium foods." })
        elif systolic < BP_LOW_WARNING[0] or diastolic < BP_LOW_WARNING[1]:
            alerts.append({ "type": "HYDRATION_REMINDER", "title": "Low Blood Pressure", "message": "Your BP is a bit low. Ensure you are well-hydrated and not skipping meals." })
        else:
            alerts.append({ "type": "POSITIVE_FEEDBACK", "title": "Blood Pressure is Normal", "message": "Great job! Your blood pressure reading is in the healthy range." })

    # Hydration Analysis
    if water is not None:
        if water < MIN_WATER_INTAKE_LITERS:
            alerts.append({ "type": "HYDRATION_REMINDER", "title": "Stay Hydrated!", "message": f"You're below the recommended {MIN_WATER_INTAKE_LITERS}L. Let's try to drink one more glass!" })
        else:
            alerts.append({ "type": "POSITIVE_FEEDBACK", "title": "Good Hydration!", "message": f"Excellent! Your water intake of {water}L is on track."})

    # Mood Analysis
    if mood is not None:
        if mood <= MOOD_LOW_THRESHOLD:
            alerts.append({ "type": "MENTAL_HEALTH_SUPPORT", "title": "Checking In", "message": "We noticed your mood was low. Remember to be kind to yourself and consider a relaxing activity." })
        else:
            alerts.append({ "type": "POSITIVE_FEEDBACK", "title": "Positive Outlook!", "message": "Glad to see you're feeling well today!"})

    # Symptom Analysis with Gemini
    if symptoms_str:
        prompt = f"A pregnant user reports these symptoms: '{symptoms_str}'. In a supportive tone, briefly explain potential concerns and recommend precautions. DO NOT DIAGNOSE. Always advise consulting a doctor for any symptoms."
        try:
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}]
            }
            headers = {'Content-Type': 'application/json'}
            url_with_key = f"{GEMINI_API_URL}?key={API_KEY}"
            
            response = requests.post(url_with_key, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            
            result = response.json()
            model_response_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')

            if model_response_text:
                alerts.append({ "type": "SYMPTOM_INFO", "title": "Information About Your Symptoms", "message": model_response_text })
            else:
                raise ValueError("AI model returned an empty response.")

        except Exception as e:
            alerts.append({ "type": "GEMINI_ERROR", "title": "Symptom Analysis Error", "message": f"Could not analyze symptoms: {e}" })

    # Determine Overall Status
    alert_types = {alert['type'] for alert in alerts if alert}
    overall_status = "GREEN"
    if "EMERGENCY" in alert_types:
        overall_status = "RED"
    elif any(t in ["DIET_WARNING", "HYDRATION_REMINDER", "MENTAL_HEALTH_SUPPORT", "SYMPTOM_INFO"] for t in alert_types):
        overall_status = "ORANGE"

    # Save to database
    try:
        new_log = WellnessLog(
            patient_id=current_user.id,
            systolic=systolic,
            diastolic=diastolic,
            water_liters=water,
            mood=mood,
            symptoms=symptoms_str,
            overall_status=overall_status
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {e}'}), 500

    # Here you could trigger real SMS for EMERGENCY alerts
    # For now, it's just part of the feedback.

    return jsonify({'alerts': alerts, 'overall_status': overall_status})

@app.route('/patient/doula', methods=['GET', 'POST'])
@login_required
def digital_doula():
    if session.get('user_type') != 'patient': return redirect(url_for('home'))

    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            # Log patient message
            db.session.add(DigitalDoulaLog(patient_id=current_user.id, message_from='patient', content=content))
            
            # Get AI response
            history = DigitalDoulaLog.query.filter_by(patient_id=current_user.id).order_by(DigitalDoulaLog.timestamp).all()
            chat_history_formatted = [{'role': 'user' if h.message_from == 'patient' else 'model', 'parts': [{'text': h.content}]} for h in history]
            
            system_prompt = "You are a Digital Doula, a supportive, empathetic AI companion for pregnant and postpartum individuals. Your tone is warm, encouraging, and informative, but never clinical. You are not a doctor. Always prioritize emotional support. Ask open-ended questions. Keep responses concise and friendly."
            payload = {"contents": chat_history_formatted, "systemInstruction": {"parts": [{"text": system_prompt}]}}
            headers = {'Content-Type': 'application/json'}
            url_with_key = f"{GEMINI_API_URL}?key={API_KEY}"
            
            try:
                response = requests.post(url_with_key, headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                result = response.json()
                ai_reply = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "I'm here to listen.")
                db.session.add(DigitalDoulaLog(patient_id=current_user.id, message_from='ai', content=ai_reply))
                db.session.commit()
            except Exception as e:
                print(f"Doula AI Error: {e}")
                # Don't crash, just fail silently or log

        return redirect(url_for('digital_doula'))

    chat_logs = DigitalDoulaLog.query.filter_by(patient_id=current_user.id).order_by(DigitalDoulaLog.timestamp.asc()).all()
    return render_template('digital_doula.html', chat_logs=chat_logs)

@app.route('/patient/doula/trigger', methods=['POST'])
@login_required
def trigger_doula_checkin():
    """Simulates a cron job triggering a proactive AI check-in."""
    if session.get('user_type') != 'patient': return redirect(url_for('home'))

    if not current_user.due_date:
        flash("Due date not set, can't provide a personalized check-in.", "warning")
        return redirect(url_for('patient_dashboard'))

    weeks_pregnant = (40 - (current_user.due_date - datetime.utcnow().date()).days / 7)
    prompt = ""
    if weeks_pregnant <= 13:
        prompt = "You are a Digital Doula. The user is in their first trimester. Proactively start a conversation by asking them how they are feeling physically or emotionally this week. Be warm and brief."
    elif 14 <= weeks_pregnant <= 27:
        prompt = "You are a Digital Doula. The user is in their second trimester. Proactively start a conversation. Ask them if they've felt the baby move yet, or how their energy levels are. Be encouraging and brief."
    else:
        prompt = "You are a Digital Doula. The user is in their third trimester. Proactively start a conversation. Gently ask if they have any questions about preparing for birth or what's on their mind as they get closer. Be reassuring and brief."

    try:
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        headers = {'Content-Type': 'application/json'}
        url_with_key = f"{GEMINI_API_URL}?key={API_KEY}"
        response = requests.post(url_with_key, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        ai_message = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')

        if ai_message:
            db.session.add(DigitalDoulaLog(patient_id=current_user.id, message_from='ai', content=ai_message))
            db.session.commit()
            flash("The AI Digital Doula has sent you a new message!", "info")
            return redirect(url_for('digital_doula'))

    except Exception as e:
        flash(f"Could not trigger AI check-in: {e}", "danger")
    
    return redirect(url_for('patient_dashboard'))

@app.route('/documents/view/<int:doc_id>')
@login_required
def view_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    # Security check
    if session['user_type'] == 'patient' and doc.patient_id != current_user.id:
        return "Unauthorized", 403
    if session['user_type'] == 'doctor' and doc.patient.doctor_id != current_user.id:
        return "Unauthorized", 403
    
    from flask import Response
    return Response(doc.file_data, mimetype=doc.mime_type, headers={
        "Content-Disposition": f"inline; filename={doc.file_name}"
    })

@app.route('/api/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, user_type=session['user_type']).order_by(Notification.timestamp.desc()).limit(10).all()
    
    # Mark fetched notifications as read
    for n in notifications: n.is_read = True
    db.session.commit()
    return jsonify({'notifications': [{'message': n.message, 'link_url': n.link_url, 'is_read': n.is_read} for n in notifications]})

@app.route('/resources')
@login_required
def resources():
    articles = Article.query.order_by(Article.publish_date.desc()).all()
    return render_template('resources.html', articles=articles)

@app.route('/resources/article/<int:article_id>')
@login_required
def view_article(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('article_view.html', article=article)

@app.route('/messages')
@login_required
def messages():
    user_id = current_user.id
    user_type = session['user_type']

    # Find all messages sent or received by the current user
    sent_messages = Message.query.filter_by(sender_id=user_id, sender_type=user_type).all()
    received_messages = Message.query.filter_by(receiver_id=user_id, receiver_type=user_type).all()
    all_messages = sorted(sent_messages + received_messages, key=operator.attrgetter('timestamp'), reverse=True)

    # Group messages by conversation partner
    conversations = {}
    for msg in all_messages:
        other_user_key = None
        if msg.sender_id == user_id and msg.sender_type == user_type:
            other_user_key = (msg.receiver_type, msg.receiver_id)
        else:
            other_user_key = (msg.sender_type, msg.sender_id)

        if other_user_key not in conversations:
            other_user_obj = Doctor.query.get(other_user_key[1]) if other_user_key[0] == 'doctor' else Patient.query.get(other_user_key[1])
            if other_user_obj:
                conversations[other_user_key] = {'user': other_user_obj, 'last_message': msg}

    # We only need the user object and the last message for the list view
    conversation_list = {v['user']: v['last_message'] for k, v in conversations.items()}
    return render_template('messages.html', conversations=conversation_list)

@app.route('/messages/conversation/<user_type>/<int:user_id>', methods=['GET', 'POST'])
@login_required
def conversation(user_type, user_id):
    current_user_id = current_user.id
    current_user_type = session['user_type']

    # Find the other user in the conversation
    other_user = None
    if user_type == 'doctor':
        other_user = Doctor.query.get_or_404(user_id)
    elif user_type == 'patient':
        other_user = Patient.query.get_or_404(user_id)
    
    if not other_user:
        flash('Conversation partner not found.', 'danger')
        return redirect(url_for('messages'))

    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            new_message = Message(
                sender_id=current_user_id,
                sender_type=current_user_type,
                receiver_id=user_id,
                receiver_type=user_type,
                content=content
            )
            db.session.add(new_message)

            # Create notification for the receiver
            notification = Notification(
                user_id=user_id, user_type=user_type,
                message=f'New message from {current_user.name}.',
                link_url=url_for('conversation', user_type=current_user_type, user_id=current_user_id)
            )
            db.session.add(notification)
            db.session.add(new_message)
            db.session.commit()
            return redirect(url_for('conversation', user_type=user_type, user_id=user_id))

    # Fetch all messages for this conversation
    messages_sent = Message.query.filter_by(sender_id=current_user_id, sender_type=current_user_type, receiver_id=user_id, receiver_type=user_type)
    messages_received = Message.query.filter_by(sender_id=user_id, sender_type=user_type, receiver_id=current_user_id, receiver_type=current_user_type)
    all_messages = sorted(messages_sent.union(messages_received).all(), key=operator.attrgetter('timestamp'))

    return render_template('conversation.html', messages=all_messages, other_user=other_user)

@app.route('/doctor/appointments')
@login_required
def doctor_appointments():
    if session.get('user_type') != 'doctor': return redirect(url_for('home'))
    
    appointments = Appointment.query.filter_by(doctor_id=current_user.id).order_by(Appointment.appointment_time.desc()).all()
    return render_template('doctor_appointments.html', appointments=appointments)

@app.route('/api/appointments/confirm/<int:appointment_id>', methods=['POST'])
@login_required
def confirm_appointment(appointment_id):
    if session.get('user_type') != 'doctor': return jsonify({'error': 'Unauthorized'}), 403
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.doctor_id != current_user.id: return jsonify({'error': 'Unauthorized'}), 403
    appt.status = 'confirmed'
    db.session.commit()

    # Create notification for patient
    notification = Notification(
        user_id=appt.patient_id, user_type='patient',
        message=f'Your appointment for {appt.appointment_time.strftime("%b %d")} is confirmed.',
        link_url=url_for('patient_appointments')
    )
    db.session.add(notification)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/appointments/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    if session.get('user_type') != 'doctor': return jsonify({'error': 'Unauthorized'}), 403
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.doctor_id != current_user.id: return jsonify({'error': 'Unauthorized'}), 403
    appt.status = 'cancelled'
    db.session.commit()

    # Create notification for patient
    notification = Notification(
        user_id=appt.patient_id, user_type='patient',
        message=f'Your appointment for {appt.appointment_time.strftime("%b %d")} was cancelled.',
        link_url=url_for('patient_appointments')
    )
    db.session.add(notification)
    db.session.commit()
    return jsonify({'success': True})

# ==============================================================================
# 7. DOCTOR PORTAL ROUTES
# ==============================================================================

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if session.get('user_type') != 'doctor':
        return redirect(url_for('home'))
    
    search_query = request.args.get('search', '')
    if search_query:
        patients = Patient.query.filter(Patient.name.ilike(f'%{search_query}%'), Patient.doctor_id == current_user.id).all()
    else:
        patients = current_user.patients
        
    return render_template('doctor_dashboard.html', doctor=current_user, patients=patients, search_query=search_query)

@app.route('/doctor/patient/<int:patient_id>')
@login_required
def doctor_view_patient(patient_id):
    if session.get('user_type') != 'doctor':
        return redirect(url_for('home'))
    
    patient = Patient.query.get_or_404(patient_id)
    if patient.doctor_id != current_user.id:
        flash('You are not authorized to view this patient.', 'danger')
        return redirect(url_for('doctor_dashboard'))

    # Fetch wellness logs for the patient, ordered by most recent
    logs = WellnessLog.query.filter_by(patient_id=patient.id).order_by(WellnessLog.log_date.desc()).all()

    # Prepare data for charts
    chart_data = {
        'labels': [log.log_date.strftime('%b %d') for log in reversed(logs)],
        'systolic': [log.systolic for log in reversed(logs)],
        'diastolic': [log.diastolic for log in reversed(logs)],
        'water': [log.water_liters for log in reversed(logs)],
        'mood': [log.mood for log in reversed(logs)],
    }

    # Add a link to the prescriptions page in the quick actions
    DOCTOR_VIEW_PATIENT_HTML_UPDATED = DOCTOR_VIEW_PATIENT_HTML.replace(
        '<!-- PRESCRIPTION_LINK_PLACEHOLDER -->',
        """
        <a href="{prescriptions_url}" class="btn btn-outline-info mt-2"><i class="bi bi-prescription2 me-2"></i>Manage Prescriptions</a>
        <a href="{documents_url}" class="btn btn-outline-secondary mt-2"><i class="bi bi-folder me-2"></i>View Documents</a>
        """.format(prescriptions_url=url_for('doctor_prescriptions', patient_id=patient.id),
                   documents_url=url_for('doctor_patient_documents', patient_id=patient.id))
    )
    TEMPLATES['doctor_view_patient.html'] = DOCTOR_VIEW_PATIENT_HTML_UPDATED + DOCTOR_VIEW_PATIENT_LOGS_HTML
    return render_template('doctor_view_patient.html', patient=patient, logs=logs, chart_data=json.dumps(chart_data))

@app.route('/doctor/patient/add', methods=['GET', 'POST'])
@login_required
def doctor_add_patient():
    if session.get('user_type') != 'doctor':
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        form_data = request.form
        if not all([form_data.get(k) for k in ['name', 'email', 'password', 'mobile', 'dob']]):
            flash('All fields are required.', 'danger')
            return render_template('doctor_add_patient.html')
        
        if Patient.query.filter_by(email=form_data.get('email')).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('doctor_add_patient.html')

        try:
            new_patient = Patient(
                name=form_data.get('name'),
                email=form_data.get('email'),
                password_hash=generate_password_hash(form_data.get('password')),
                mobile=form_data.get('mobile'),
                dob=datetime.strptime(form_data.get('dob'), '%Y-%m-%d').date(),
                blood_group=form_data.get('blood_group'),
                allergies=form_data.get('allergies'),
                current_medications=form_data.get('current_medications'),
                previous_pregnancies=form_data.get('previous_pregnancies'),
                due_date=datetime.strptime(form_data.get('due_date'), '%Y-%m-%d').date() if form_data.get('due_date') else None,
                address=form_data.get('address'),
                emergency_contact_name=form_data.get('emergency_contact_name'),
                emergency_contact_phone=form_data.get('emergency_contact_phone'),
                doctor_id=current_user.id
            )
            db.session.add(new_patient)
            db.session.commit()
            flash(f'Patient {form_data.get("name")} has been successfully added.', 'success')
            return redirect(url_for('doctor_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')

    return render_template('doctor_add_patient.html')

@app.route('/doctor/patient/edit/<int:patient_id>', methods=['POST'])
@login_required
def doctor_edit_patient(patient_id):
    if session.get('user_type') != 'doctor':
        return redirect(url_for('home'))
    
    patient = Patient.query.get_or_404(patient_id)
    if patient.doctor_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('doctor_dashboard'))

    patient.medical_history = request.form.get('medical_history', patient.medical_history)
    patient.current_status = request.form.get('current_status', patient.current_status)
    db.session.commit()
    flash(f"Details for {patient.name} have been updated.", 'success')
    return redirect(url_for('doctor_view_patient', patient_id=patient.id))

@app.route('/doctor/patient/<int:patient_id>/prescriptions', methods=['GET', 'POST'])
@login_required
def doctor_prescriptions(patient_id):
    if session.get('user_type') != 'doctor': return redirect(url_for('home'))
    patient = Patient.query.get_or_404(patient_id)
    if patient.doctor_id != current_user.id: return redirect(url_for('doctor_dashboard'))

    prescriptions = Prescription.query.filter_by(patient_id=patient.id).order_by(Prescription.prescribed_date.desc()).all()
    return render_template('doctor_prescriptions.html', patient=patient, prescriptions=prescriptions)

@app.route('/doctor/patient/<int:patient_id>/prescriptions/add', methods=['POST'])
@login_required
def doctor_add_prescription(patient_id):
    if session.get('user_type') != 'doctor': return redirect(url_for('home'))
    patient = Patient.query.get_or_404(patient_id)
    if patient.doctor_id != current_user.id: return redirect(url_for('doctor_dashboard'))
    
    new_rx = Prescription(patient_id=patient.id, doctor_id=current_user.id, medication=request.form['medication'], dosage=request.form['dosage'], frequency=request.form['frequency'], notes=request.form['notes'])
    db.session.add(new_rx)
    db.session.commit()
    flash('Prescription added successfully.', 'success')
    return redirect(url_for('doctor_prescriptions', patient_id=patient.id))

DOCTOR_VIEW_PATIENT_LOGS_HTML = """
<div class="card mt-4">
    <div class="card-header" data-bs-toggle="collapse" href="#wellnessCharts" role="button" aria-expanded="false" aria-controls="wellnessCharts">
        <h5><i class="bi bi-clipboard2-data-fill me-2"></i>Wellness Log History</h5>
    </div>
    {% if logs %}<div class="list-group list-group-flush">
        {% for log in logs %}
        <div class="list-group-item">
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">Log for {{ log.log_date.strftime('%Y-%m-%d') }}</h6>
                <span class="badge 
                    {% if log.overall_status == 'RED' %}bg-danger
                    {% elif log.overall_status == 'ORANGE' %}bg-warning text-dark
                    {% else %}bg-success{% endif %}
                ">{{ log.overall_status }}</span>
            </div>
            <small>
                {% if log.systolic and log.diastolic %}<strong>BP:</strong> {{ log.systolic }}/{{ log.diastolic }} mmHg | {% endif %}
                {% if log.water_liters is not none %}<strong>Water:</strong> {{ log.water_liters }}L | {% endif %}
                {% if log.mood %}<strong>Mood:</strong> {{ log.mood }}/5 | {% endif %}
                {% if log.symptoms %}<strong>Symptoms:</strong> {{ log.symptoms }}{% endif %}
            </small>
        </div>
        {% endfor %}
    </div>
    {% else %}<div class="card-body">
        <p class="text-muted">No wellness logs have been submitted by this patient yet.</p>
    </div>
    {% endif %}
</div><script>
    document.addEventListener('DOMContentLoaded', function() {
        const chartData = JSON.parse('{{ chart_data|safe }}');
        
        // Blood Pressure Chart
        const bpCtx = document.getElementById('bpChart').getContext('2d');
        new Chart(bpCtx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Systolic',
                    data: chartData.systolic,
                    borderColor: 'rgb(232, 149, 167)',
                    tension: 0.1
                }, {
                    label: 'Diastolic',
                    data: chartData.diastolic,
                    borderColor: 'rgb(108, 117, 125)',
                    tension: 0.1
                }]
            }
        });

        // Mood and Water Chart
        const moodWaterCtx = document.getElementById('moodWaterChart').getContext('2d');
        new Chart(moodWaterCtx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Water Intake (L)',
                    data: chartData.water,
                    borderColor: 'rgb(54, 162, 235)',
                    tension: 0.1
                }, {
                    label: 'Mood (1-5)',
                    data: chartData.mood,
                    borderColor: 'rgb(255, 205, 86)',
                    tension: 0.1
                }]
            }
        });
    });
</script>
"""

@app.route('/doctor/patient/<int:patient_id>/logs')
@login_required
def doctor_view_patient_logs(patient_id):
    # This is a placeholder if you want a separate page, but for now we include it in the main view
    # The logic is now inside doctor_view_patient
    return redirect(url_for('doctor_view_patient', patient_id=patient_id))


@app.route('/doctor/patient/<int:patient_id>/documents')
@login_required
def doctor_patient_documents(patient_id):
    if session.get('user_type') != 'doctor':
        return redirect(url_for('home'))

    patient = Patient.query.get_or_404(patient_id)
    if patient.doctor_id != current_user.id:
        flash('You are not authorized to view this patient.', 'danger')
        return redirect(url_for('doctor_dashboard'))

    documents = Document.query.filter_by(patient_id=patient.id).order_by(Document.upload_date.desc()).all()
    return render_template('doctor_patient_documents.html', patient=patient, documents=documents)

# ==============================================================================
# 8. INITIAL DATABASE SETUP
# ==============================================================================

def create_initial_data():
    """Creates sample doctors and patients if the database is empty."""
    with app.app_context():
        # Create tables if they don't exist (commented out drop_all for safety)
        print("Initializing database schema...")
        # db.drop_all()  # Commented out to avoid losing data in production
        try:
            db.create_all()
            print("Database schema created/verified.")
        except Exception as e:
            print(f"Database already initialized or error occurred: {e}")
        
        # Check if the doctor table is empty before seeding
        if not Doctor.query.first():
            print("Database is empty. Seeding with initial data...")
            doctor1 = Doctor(
                name="Dr. Emily Carter",
                mobile="5550001111",
                password_hash=generate_password_hash("password_placeholder")
            )
            db.session.add(doctor1)
            
            patient1 = Patient(
                name="Jane Doe",
                email="jane.doe@example.com",
                password_hash=generate_password_hash("password123"),
                mobile="5551234567",
                address="123 Wellness Ave, Healthville",
                dob=datetime.strptime("1995-05-20", "%Y-%m-%d").date(),
                due_date=datetime.strptime("2025-03-15", "%Y-%m-%d").date(),
                medical_history="Mild asthma, controlled with inhaler.",
                current_status="24 weeks pregnant, progressing normally. Next appointment in 2 weeks.",
                emergency_contact_name="John Doe (Husband)",
                emergency_contact_phone="5557654321",
                doctor=doctor1
            )
            db.session.add(patient1)
            
            # Seed articles
            article1 = Article(
                title="Nutrition During Pregnancy: What to Eat",
                content="A balanced diet is crucial during pregnancy. Focus on whole foods like fruits, vegetables, lean proteins, and whole grains. Folate, iron, and calcium are particularly important. Avoid raw fish, unpasteurized dairy, and excessive caffeine.",
                category="Nutrition"
            )
            article2 = Article(
                title="Understanding the First Trimester",
                content="The first trimester (weeks 1-12) is a time of rapid development for your baby. You may experience morning sickness, fatigue, and hormonal changes. It's important to start prenatal care and take folic acid supplements.",
                category="First Trimester"
            )
            article3 = Article(
                title="Safe Exercises for Expecting Mothers",
                content="Staying active is beneficial. Gentle exercises like walking, swimming, and prenatal yoga are excellent choices. Always listen to your body and avoid high-impact sports or activities with a risk of falling. Consult your doctor before starting any new exercise routine.",
                category="Exercise"
            )
            article4 = Article(
                title="Navigating the Second Trimester",
                content="Often called the 'honeymoon' phase of pregnancy, the second trimester (weeks 14-27) may bring renewed energy. This is a great time to focus on healthy eating and gentle exercise. You'll also likely feel your baby's first movements!",
                category="Second Trimester"
            )
            article5 = Article(
                title="Preparing for Labor in the Third Trimester",
                content="As you enter the third trimester (week 28 onwards), it's time to prepare for labor. Learn about the signs of labor, create a birth plan, and pack your hospital bag. Regular check-ups become more frequent now.",
                category="Third Trimester"
            )
            db.session.add_all([article1, article2, article3, article4, article5])

            db.session.commit()
            print("Initial data created successfully.")
        else:
            print("Database already contains data. Skipping seeding.")

# ==============================================================================
# 9. APPLICATION RUNNER
# ==============================================================================

if __name__ == '__main__':
    # The create_initial_data function will handle table creation and seeding
    create_initial_data()
    app.run(debug=True)