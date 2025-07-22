from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date
import base64
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Person(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    employee_id: str
    face_descriptor: str  # Base64 encoded face descriptor from face-api.js
    photo: str  # Base64 encoded photo
    role: str = "employee"  # employee, student
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PersonCreate(BaseModel):
    name: str
    employee_id: str
    face_descriptor: str
    photo: str
    role: str = "employee"

class AttendanceRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    person_id: str
    person_name: str
    employee_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    confidence: float
    photo: Optional[str] = None  # Base64 encoded photo of person at time of recognition

class AttendanceCreate(BaseModel):
    person_id: str
    person_name: str
    employee_id: str
    confidence: float
    photo: Optional[str] = None

class AttendanceStats(BaseModel):
    total_registered: int
    present_today: int
    absent_today: int
    attendance_rate: float

# Person Management Routes
@api_router.post("/persons", response_model=Person)
async def create_person(person_data: PersonCreate):
    """Register a new person with their face data"""
    try:
        # Check if employee_id already exists
        existing_person = await db.persons.find_one({"employee_id": person_data.employee_id})
        if existing_person:
            raise HTTPException(status_code=400, detail="Employee ID already exists")
        
        person_dict = person_data.dict()
        person_obj = Person(**person_dict)
        
        await db.persons.insert_one(person_obj.dict())
        return person_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating person: {str(e)}")

@api_router.get("/persons", response_model=List[Person])
async def get_all_persons():
    """Get all registered persons"""
    try:
        persons = await db.persons.find().to_list(1000)
        return [Person(**person) for person in persons]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching persons: {str(e)}")

@api_router.get("/persons/{person_id}", response_model=Person)
async def get_person(person_id: str):
    """Get a specific person by ID"""
    try:
        person = await db.persons.find_one({"id": person_id})
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        return Person(**person)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching person: {str(e)}")

@api_router.delete("/persons/{person_id}")
async def delete_person(person_id: str):
    """Delete a person"""
    try:
        result = await db.persons.delete_one({"id": person_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Person not found")
        
        # Also delete their attendance records
        await db.attendance.delete_many({"person_id": person_id})
        
        return {"message": "Person and their attendance records deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting person: {str(e)}")

# Attendance Routes
@api_router.post("/attendance", response_model=AttendanceRecord)
async def mark_attendance(attendance_data: AttendanceCreate):
    """Mark attendance for a recognized person"""
    try:
        # Check if person exists
        person = await db.persons.find_one({"id": attendance_data.person_id})
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        # Check if already marked present today
        today = datetime.now().strftime("%Y-%m-%d")
        existing_attendance = await db.attendance.find_one({
            "person_id": attendance_data.person_id,
            "date": today
        })
        
        if existing_attendance:
            raise HTTPException(status_code=400, detail="Attendance already marked for today")
        
        attendance_dict = attendance_data.dict()
        attendance_obj = AttendanceRecord(**attendance_dict)
        
        await db.attendance.insert_one(attendance_obj.dict())
        return attendance_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking attendance: {str(e)}")

@api_router.get("/attendance/today", response_model=List[AttendanceRecord])
async def get_today_attendance():
    """Get today's attendance records"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        attendance_records = await db.attendance.find({"date": today}).to_list(1000)
        return [AttendanceRecord(**record) for record in attendance_records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching today's attendance: {str(e)}")

@api_router.get("/attendance/stats", response_model=AttendanceStats)
async def get_attendance_stats():
    """Get attendance statistics"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        
        total_registered = await db.persons.count_documents({})
        present_today = await db.attendance.count_documents({"date": today})
        absent_today = max(0, total_registered - present_today)
        
        attendance_rate = (present_today / total_registered * 100) if total_registered > 0 else 0
        
        return AttendanceStats(
            total_registered=total_registered,
            present_today=present_today,
            absent_today=absent_today,
            attendance_rate=round(attendance_rate, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@api_router.get("/attendance/history/{person_id}")
async def get_person_attendance_history(person_id: str):
    """Get attendance history for a specific person"""
    try:
        attendance_records = await db.attendance.find({"person_id": person_id}).sort("timestamp", -1).to_list(100)
        return [AttendanceRecord(**record) for record in attendance_records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching attendance history: {str(e)}")

@api_router.get("/attendance/date/{date_str}")
async def get_attendance_by_date(date_str: str):
    """Get attendance records for a specific date (YYYY-MM-DD)"""
    try:
        attendance_records = await db.attendance.find({"date": date_str}).to_list(1000)
        return [AttendanceRecord(**record) for record in attendance_records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching attendance for date: {str(e)}")

# Health check
@api_router.get("/")
async def root():
    return {"message": "Face Recognition Attendance System API", "status": "active"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()