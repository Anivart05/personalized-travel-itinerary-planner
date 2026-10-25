# ✈️ Personalized Travel Itinerary Planner (WanderAI)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Flask](https://img.shields.io/badge/Alternative-Flask_3.x-black.svg?style=flat&logo=flask)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB.svg?style=flat&logo=react)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/UI-Tailwind_CSS-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E.svg?style=flat&logo=supabase)](https://supabase.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat&logo=python)](https://www.python.org/)

An AI-powered full-stack web application that automates travel planning and eliminates decision fatigue. Built with **FastAPI**, **React**, and **Supabase**, it generates personalized day-by-day itineraries with attractions, dining, accommodations, and transit logistics tailored to user budget, pace, and travel style.

---

## 🌟 Key Features

- **⚡ Smart AI Trip Builder**: Capture destination, dates, budget tier, travel style (Solo, Couple, Group), group size, pace, and interests.
- **🔄 Dynamic Day Regeneration**: Modify and regenerate individual days with custom instructions (e.g., *"more scenic outdoor spots, less museum walking"*).
- **🗺️ Interactive Route Map**: Integrated OpenStreetMap & Leaflet interactive map displaying day stops with route lines.
- **💰 Real-Time Budget Analytics**: Categorized cost breakdowns (stays, dining, attractions, transit) with budget adherence tracking.
- **🤖 AI Travel Copilot**: In-app assistant providing personalized answers for packing lists, local transit, eSIMs, and emergency customs.
- **🔗 1-Click Group Sharing**: Shareable public link tokens for collaborative planning.

---

## 🧭 Preconfigured Scenarios

| Scenario | Target Traveler | Focus & Solution |
| :--- | :--- | :--- |
| **Scenario 1: Solo Getaway** | Solo Traveler (Paris • 3 Days) | Tight walkable routes, famous monuments, and safe evening dining with zero planning time. |
| **Scenario 2: Romantic Vacation** | Couple (Amalfi Coast • 6 Days) | Relaxed pace, scenic coastal viewpoints, intimate dining, and interactive day regeneration. |
| **Scenario 3: Small Group Adventure** | 4 Friends (Tokyo • 6 Days) | Balanced group interests (culture, digital art, nightlife) with centralized shared budget tracking. |

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI (Asynchronous REST API), Flask 3.x (companion implementation), Pydantic v2.
- **Frontend**: React 18, Tailwind CSS, Lucide Icons, Leaflet / OpenStreetMap.
- **Database**: Supabase PostgreSQL (Cloud) with automatic SQLite local fallback (`itineraries.db`).
- **AI & Optimization**: Multi-provider engine (Google Gemini API, OpenAI GPT-4o-mini, and built-in Geo-Knowledge Engine) + Haversine distance & transit optimization.

---

## 📂 Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI server & static frontend serving
│   │   ├── config.py            # Environment settings
│   │   ├── models/schemas.py    # Pydantic data schemas
│   │   ├── services/
│   │   │   ├── ai_generator.py  # Generative AI & prompt engineering engine
│   │   │   ├── optimizer.py     # Route transit & budget optimization
│   │   │   └── database.py      # Supabase & SQLite integration
│   │   ├── api/
│   │   │   ├── trips.py         # Trip generation, editing, & day regeneration
│   │   │   ├── auth.py          # User authentication endpoints
│   │   │   └── scenarios.py     # Scenario 1, 2, 3 quick presets
│   │   └── static/              # React SaaS dashboard (HTML, CSS, JS)
│   ├── flask_app/app.py         # Companion Flask implementation
│   ├── tests/                   # 10 automated unit & integration tests
│   ├── requirements.txt         # Backend Python dependencies
│   └── run.py                   # 1-click startup script
├── frontend/                    # Standalone React Vite project source
├── supabase/
│   └── schema.sql               # Supabase PostgreSQL migration script
├── Dockerfile                   # Docker containerization
├── docker-compose.yml           # Multi-container orchestration
├── requirements.txt             # Root dependencies
└── README.md
