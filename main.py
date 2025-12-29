from fastapi import FastAPI, HTTPException          # Web framework + error handling
from fastapi.middleware.cors import CORSMiddleware  # CORS (like rack-cors)
from sqlalchemy import create_engine, Column, Integer, String, DateTime  # Database
from sqlalchemy.orm import sessionmaker, declarative_base  # ORM (like ActiveRecord)
from pydantic import BaseModel                      # Request/response validation
from datetime import datetime
from typing import Optional                         # For optional fields

# FastAPI app
app = FastAPI()

# CORS (like rack-cors in Rails)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup (SQLite)
engine = create_engine("sqlite:///photos.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# Model (like app/models/photo.rb)
class Photo(Base):
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create tables (like rails db:create + rails db:migrate combined)
Base.metadata.create_all(bind=engine)


# Pydantic schemas (for request/response validation)
class PhotoCreate(BaseModel):
    name: str
    url: str
    width: Optional[int] = None
    height: Optional[int] = None


class PhotoUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class PhotoResponse(BaseModel):
    id: int
    name: str
    url: str
    width: Optional[int]
    height: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows converting SQLAlchemy model to Pydantic


# Seed data (like db/seeds.rb)
def seed_data():
    db = SessionLocal()
    if db.query(Photo).count() == 0:
        photos = [
            Photo(name="Mountain Lake", url="https://via.placeholder.com/400X300", width=400, height=300),
            Photo(name="City Skyline", url="https://via.placeholder.com/400X300", width=400, height=300)
        ]
        db.add_all(photos)
        db.commit()
        print("Sample photos created!")
    db.close()

# Run on startup
seed_data()

# INDEX - GET /photos
@app.get("/photos", response_model=list[PhotoResponse])
def index():
    db = SessionLocal()
    photos = db.query(Photo).all() # Like Photo.all in Rails
    db.close()
    return photos

#CREATE -POST /photos
@app.post("/photos", response_model=PhotoResponse, status_code=201)
def create(photo_data: PhotoCreate):
    db = SessionLocal()
    photo = Photo(**photo_data.model_dump()) 
    db.add(photo)
    db.commit()
    db.refresh(photo)
    db.close()
    return photo

#SHOW - GET /photos/{id}
@app.get("/photos/{id}", response_model=PhotoResponse)
def show(id: int):
    db = SessionLocal()
    photo = db.query(Photo).filter(Photo.id == id).first()          # Like Photo.find(id)
    db.close()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo

# UPDATE - PATCH /photos/{id}
@app.patch("/photos/{id}", response_model=PhotoResponse)
def update(id: int, photo_data: PhotoUpdate):
    db = SessionLocal()
    photo = db.query(Photo).filter(Photo.id==id).first()
    if not photo:
        db.close()
        raise HTTPException(status_code=404, detail="Photo not found")
    
    update_data = photo_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(photo, key, value)

    db.commit()
    db.refresh(photo)
    db.close()
    return photo


