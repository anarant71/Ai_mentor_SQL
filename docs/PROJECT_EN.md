# AI Mentor Project Documentation

## 1. Overview

AI Mentor is a personal AI tutor for learning analytics, SQL, product logic, and practical projects. The system doesn't just show lessons, but builds an individual learning trajectory, assesses the student's level, tracks skills, records typical mistakes, selects assignments, and helps bring learning projects to completion.

The key idea of the project: each student has a dynamic competency profile. Based on this, the AI tutor decides what to provide next: explanation, training, SQL task, practice of weak skills, project work, or level assessment.

## 2. Target Capabilities

- Skills system `skills`
- Mistakes system `mistakes`
- Personal roadmaps for each student
- SQL Sandbox for executing educational SQL queries
- Educational projects system
- Adaptive learning
- Student level assessment
- AI tutor with context on progress, mistakes, projects, and goals
- Automations through n8n for reminders, reports, and regular checks

## 3. System Architecture

The system consists of several components:

- Frontend - student's personal dashboard
- Backend API - business logic and data management
- AI Mentor Engine - context-aware AI assistant
- Databases - PostgreSQL for main data, read-only for SQL Sandbox
- n8n - workflow automation platform

## 4. Data Model

The system uses a PostgreSQL database with the following main entities:

- Users - system users (students, mentors, admins)
- Student profiles - additional information about students
- Skills - catalog of skills
- Student skills - student's skill levels
- Lessons - educational content
- Tasks - educational assignments
- Submissions - student responses to tasks
- Roadmaps - personal learning plans
- Roadmap steps - individual learning steps
- Mentor conversations - dialogues with the AI tutor
- Mentor messages - messages in dialogues

## 5. User Roles

The system supports several user roles:

- Student - primary user, learning the material
- Mentor - AI assistant
- Admin - system administrator

## 6. Development Plan

1. Core system implementation
2. User authentication and authorization
3. Basic educational content management
4. Student progress tracking
5. AI mentor integration
6. Adaptive learning algorithms
7. Reporting and analytics
8. Mobile application development