import json
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional
from ..config import settings
from ..models.schemas import TripItinerary, UserResponse

# Optional Supabase client initialization
supabase_client = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    try:
        from supabase import create_client, Client
        supabase_client: Optional[Client] = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_KEY
        )
        print("Connected successfully to Supabase.")
    except Exception as e:
        print(f"Supabase connection error: {e}. Falling back to SQLite.")
        supabase_client = None


class DatabaseService:
    def __init__(self):
        self.db_path = settings.DB_PATH
        self._init_sqlite()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        """Initialize SQLite tables for fallback & local execution."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        # Trips table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trips (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT NOT NULL,
                destination TEXT NOT NULL,
                country TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                travel_style TEXT NOT NULL,
                group_size INTEGER NOT NULL,
                budget_tier TEXT NOT NULL,
                trip_data JSON NOT NULL,
                share_token TEXT UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        conn.commit()
        conn.close()

    # ---------------- USER METHODS ----------------

    def create_user(
        self, email: str, password_hash: str, full_name: str
    ) -> UserResponse:
        user_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        if supabase_client:
            try:
                res = (
                    supabase_client.table("users")
                    .insert(
                        {
                            "id": user_id,
                            "email": email,
                            "password_hash": password_hash,
                            "full_name": full_name,
                            "created_at": created_at,
                        }
                    )
                    .execute()
                )
                if res.data:
                    row = res.data[0]
                    return UserResponse(
                        id=row["id"],
                        email=row["email"],
                        full_name=row["full_name"],
                        created_at=row["created_at"],
                    )
            except Exception as e:
                print(f"Supabase create_user error: {e}. Using SQLite fallback.")

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (id, email, password_hash, full_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, email, password_hash, full_name, created_at),
        )
        conn.commit()
        conn.close()

        return UserResponse(
            id=user_id, email=email, full_name=full_name, created_at=created_at
        )

    def get_user_by_email(self, email: str) -> Optional[dict]:
        if supabase_client:
            try:
                res = (
                    supabase_client.table("users")
                    .select("*")
                    .eq("email", email)
                    .limit(1)
                    .execute()
                )
                if res.data:
                    return res.data[0]
            except Exception as e:
                print(f"Supabase get_user_by_email error: {e}. Using SQLite.")

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    # ---------------- TRIP METHODS ----------------

    def save_trip(
        self, trip: TripItinerary, user_id: Optional[str] = None
    ) -> TripItinerary:
        trip.user_id = user_id or trip.user_id
        if not trip.share_token:
            trip.share_token = str(uuid.uuid4())[:8]

        trip_dict = trip.model_dump()
        trip_json = json.dumps(trip_dict)

        if supabase_client:
            try:
                payload = {
                    "id": trip.id,
                    "user_id": trip.user_id,
                    "title": trip.title,
                    "destination": trip.destination,
                    "country": trip.country,
                    "start_date": trip.start_date,
                    "end_date": trip.end_date,
                    "duration_days": trip.duration_days,
                    "travel_style": trip.travel_style,
                    "group_size": trip.group_size,
                    "budget_tier": trip.budget_tier,
                    "trip_data": trip_dict,
                    "share_token": trip.share_token,
                    "created_at": trip.created_at,
                    "updated_at": trip.updated_at,
                }
                supabase_client.table("trips").upsert(payload).execute()
                return trip
            except Exception as e:
                print(f"Supabase save_trip error: {e}. Falling back to SQLite.")

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO trips (
                id, user_id, title, destination, country,
                start_date, end_date, duration_days, travel_style,
                group_size, budget_tier, trip_data, share_token,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trip.id,
                trip.user_id,
                trip.title,
                trip.destination,
                trip.country,
                trip.start_date,
                trip.end_date,
                trip.duration_days,
                trip.travel_style,
                trip.group_size,
                trip.budget_tier,
                trip_json,
                trip.share_token,
                trip.created_at,
                trip.updated_at,
            ),
        )
        conn.commit()
        conn.close()
        return trip

    def get_trip(self, trip_id: str) -> Optional[TripItinerary]:
        if supabase_client:
            try:
                res = (
                    supabase_client.table("trips")
                    .select("*")
                    .eq("id", trip_id)
                    .limit(1)
                    .execute()
                )
                if res.data:
                    data = res.data[0]["trip_data"]
                    return TripItinerary(**data)
            except Exception as e:
                print(f"Supabase get_trip error: {e}. Falling back to SQLite.")

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT trip_data FROM trips WHERE id = ?", (trip_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            data = json.loads(row["trip_data"])
            return TripItinerary(**data)
        return None

    def get_trip_by_share_token(self, token: str) -> Optional[TripItinerary]:
        if supabase_client:
            try:
                res = (
                    supabase_client.table("trips")
                    .select("*")
                    .eq("share_token", token)
                    .limit(1)
                    .execute()
                )
                if res.data:
                    data = res.data[0]["trip_data"]
                    return TripItinerary(**data)
            except Exception as e:
                print(f"Supabase share token error: {e}.")

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT trip_data FROM trips WHERE share_token = ?", (token,))
        row = cursor.fetchone()
        conn.close()
        if row:
            data = json.loads(row["trip_data"])
            return TripItinerary(**data)
        return None

    def list_trips(
        self, user_id: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[TripItinerary]:
        if supabase_client:
            try:
                query = supabase_client.table("trips").select("*")
                if user_id:
                    query = query.eq("user_id", user_id)
                res = (
                    query.order("updated_at", desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )
                if res.data:
                    return [TripItinerary(**r["trip_data"]) for r in res.data]
            except Exception as e:
                print(f"Supabase list_trips error: {e}. Falling back to SQLite.")

        conn = self._get_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute(
                """
                SELECT trip_data FROM trips 
                WHERE user_id = ? 
                ORDER BY updated_at DESC LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset),
            )
        else:
            cursor.execute(
                """
                SELECT trip_data FROM trips 
                ORDER BY updated_at DESC LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            try:
                results.append(TripItinerary(**json.loads(row["trip_data"])))
            except Exception as err:
                print(f"Error parsing trip: {err}")
        return results

    def delete_trip(self, trip_id: str) -> bool:
        if supabase_client:
            try:
                supabase_client.table("trips").delete().eq("id", trip_id).execute()
            except Exception as e:
                print(f"Supabase delete error: {e}")

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted


db_service = DatabaseService()
