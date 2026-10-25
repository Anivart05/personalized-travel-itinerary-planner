# ✈️ Personalized Travel Itinerary Planner (WanderAI)

An AI-powered, full-stack travel planning platform built with **Python (FastAPI & Flask)**, a **React SaaS-style frontend**, and **Supabase / SQLite** database integration. It intelligently generates, optimizes, customizes, and regenerates day-by-day travel itineraries based on budget, travel style, pace, and interests.

---

## 🌟 Key Features & Problem Solutions

| Problem | WanderAI Solution |
| :--- | :--- |
| **Decision Fatigue & Hours of Research** | Generates a complete, structured day-by-day itinerary in seconds, tailored to individual interests and travel style. |
| **Rigid & Generic Plans** | Dynamic **Day Regeneration** allows travelers to refine specific days (e.g., "more scenic sunset spots, less museum walking"). |
| **Inefficient Routing & Logistics Delay** | Automated distance & transit estimation minimizes transit time between sequential morning, afternoon, and evening stops. |
| **Budget Overruns** | Real-time **Budget Visualizer & Analytics** tracks accommodation, dining, attraction, and transit expenses against target budgets. |
| **Group Coordination Conflicts** | Scenario 3 engine balances multi-traveler interests and provides **1-click public sharing tokens** for collaborative review. |

---

## 🧭 Preconfigured Scenario Walkthroughs

The application includes direct presets for all three user scenarios:

### 1. Solo Traveler Planning a Weekend Getaway
- **Destination:** Paris, France (3 Days)
- **Style & Pace:** Solo Traveler • Balanced Pace • Budget: \$750
- **Focus:** Highly walkable routes, famous monuments (Louvre, Eiffel, Le Marais), authentic dining, and safe evening bistros without hours of manual route planning.

### 2. Couple Planning a Personalized Vacation
- **Destination:** Amalfi Coast, Italy (6 Days)
- **Style & Pace:** Romantic Couple • Relaxed Pace • Budget: \$3,200
- **Focus:** Scenic cliffside viewpoints, intimate dining, private boat excursion options, and **interactive day regeneration** to customize individual dates.

### 3. Small Group Coordinating a Multi-Day Trip
- **Destination:** Tokyo, Japan (6 Days)
- **Style & Pace:** Small Group (4 Friends) • Fast-Paced • Budget: \$4,500
- **Focus:** Coordinated activities balancing cultural temples, teamLab digital art, nightlife in Shinjuku, and group transit optimization.

---

## 🏗️ System Architecture

```
                               ┌────────────────────────────────────────┐
                               │           React 18 Frontend            │
                               │  - Smart Trip Builder Form             │
                               │  - Interactive Day-by-Day View         │
                               │  - Leaflet / OpenStreetMap Route Map   │
                               │  - Budget Visualizer & Analytics       │
                               │  - AI Travel Copilot Assistant         │
                               └──────────────────┬─────────────────────┘
                                                  │ REST APIs / JSON
                                                  ▼
                               ┌────────────────────────────────────────┐
                               │          FastAPI / Flask Backend       │
                               │  - Pydantic Validation & Schemas       │
                               │  - REST API Routers (/trips, /auth)    │
                               │  - Itinerary Route & Budget Optimizer  │
                               │  - Multi-Provider AI Engine            │
                               └──────────┬──────────────────┬──────────┘
                                          │                  │
                         ┌────────────────┘                  └────────────────┐
                         ▼                                                    ▼
       ┌───────────────────────────────────┐               ┌───────────────────────────────────┐
       │       Generative AI Engine        │               │         Database Layer            │
       │  - Google Gemini Generative AI    │               │  - Supabase PostgreSQL (Cloud)    │
       │  - OpenAI (GPT-4o / GPT-4o-mini)  │               │  - SQLite (Local Auto-Fallback)   │
       │  - Anthropic Claude API           │               │  - User Auth & Shared Trip Tokens │
       │  - Built-in Geo-Knowledge Engine  │               └───────────────────────────────────┘
       └───────────────────────────────────┘
```

---

## 📂 Project Structure

```
travel-itinerary-planner/
├── backend/
│   ├── app/
│   │   ├── config.py              # Environment configuration & secrets
│   │   ├── main.py                # FastAPI entry point & static file serving
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic models (Trips, Days, Activities, Budget)
│   │   ├── services/
│   │   │   ├── ai_generator.py    # Generative AI engine & prompt engineering
│   │   │   ├── optimizer.py       # Distance, transit time, & budget calculation
│   │   │   └── database.py        # Supabase client with SQLite fallback
│   │   ├── api/
│   │   │   ├── trips.py           # Core trip CRUD & regeneration endpoints
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   └── scenarios.py       # Scenario 1, 2, 3 quick presets
│   │   └── static/
│   │       ├── index.html         # React SaaS dashboard container
│   │       └── app.js             # Full interactive React application
│   ├── flask_app/
│   │   └── app.py                 # Flask companion implementation
│   ├── tests/
│   │   ├── test_models.py         # Pydantic model validation tests
│   │   ├── test_ai_generator.py   # AI generation & day regeneration tests
│   │   └── test_api.py            # FastAPI endpoint tests
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py                     # 1-click launcher script
├── frontend/                      # Standalone React Vite project source
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx
│       └── api.js
├── supabase/
│   └── schema.sql                 # Complete Supabase SQL migration script
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ installed
- *(Optional)* Supabase account for cloud database storage
- *(Optional)* Google Gemini or OpenAI API key

### 2. Setup Virtual Environment & Dependencies
```bash
# Navigate to the backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(The application works out of the box with zero external configuration using the local SQLite persistence and built-in knowledge engine! If you have Gemini, OpenAI, or Supabase keys, paste them into `.env`).*

### 4. Run the Application
```bash
python run.py
```
Open your browser to:
- **Interactive Web Dashboard:** [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Flask Backend:** `python flask_app/app.py` (Runs on `http://localhost:5000`)

---

## 🗄️ Supabase Integration

To use Supabase for cloud persistence and user authentication:
1. Create a project at [supabase.com](https://supabase.com).
2. Go to the **SQL Editor** in your Supabase dashboard and run the script in `supabase/schema.sql`.
3. In your `.env` file, set:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-or-service-key
   ```
4. Restart the server. The database service automatically connects to Supabase and manages trips and users in the cloud.

---

## 🧪 Running Automated Tests

Run the full pytest suite (10 unit & integration tests):
```bash
cd backend
python -m pytest tests -v
```

Tests include:
- `test_generate_itinerary_scenario_1_solo`: Generates 3-day Paris solo plan.
- `test_regenerate_single_day_scenario_2`: Tests dynamic day-level AI regeneration.
- `test_copilot_assistant`: Tests the AI travel assistant Q&A engine.
- `test_health_check` & `test_list_scenarios`: Tests REST API routing and presets.
- `test_models`: Validates Pydantic serialization, constraints, and budget statuses.

---

## 🐳 Docker Deployment

To build and run with Docker:
```bash
docker-compose up --build
```
Access the application at `http://localhost:8000`.

---

## 📜 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/trips/generate` | Generates a new personalized itinerary with AI |
| `GET` | `/api/trips` | Lists saved itineraries |
| `GET` | `/api/trips/{trip_id}` | Retrieves full itinerary details |
| `POST` | `/api/trips/{trip_id}/regenerate-day` | Refines a single day with AI feedback |
| `POST` | `/api/trips/{trip_id}/days/{day_number}/activities` | Adds a custom activity to a day |
| `DELETE` | `/api/trips/{trip_id}/activities/{activity_id}` | Removes an activity & recalculates budget |
| `GET` | `/api/trips/share/{share_token}` | Public link for group collaboration |
| `POST` | `/api/trips/copilot` | AI copilot answering packing, visa, & local tips |
| `GET` | `/api/scenarios` | Lists Scenario 1, 2, and 3 quick presets |
| `GET` | `/api/health` | Health check & active AI provider status |
