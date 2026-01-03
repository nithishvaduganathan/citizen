from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import database
from pydantic import BaseModel
from passlib.context import CryptContext
import feedparser
from rag_chat import chat_with_rag

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Citizen App API")

# CORS Setup
origins = ["http://localhost:5173", "http://localhost:3000","http://localhost:5174","http://192.168.43.56:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Utils
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Pydantic Models
from fastapi.staticfiles import StaticFiles
import base64
import uuid
import os

# Create uploads directory
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ... (Auth Utils remain same) ...

# Pydantic Models
# Pydantic Models
class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    profile_image: Optional[str] = None # Base64 encoded string
    role: str = "citizen"
    department: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    sub_district: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    profile_image_path: Optional[str] = None
    role: str
    department: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    sub_district: Optional[str] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    profile_image: Optional[str] = None # Base64

import datetime

class ReportCreate(BaseModel):
    title: str
    description: str
    location: str
    image: Optional[str] = None # Base64
    tags: List[str]
    user_id: int 

class ReportResolve(BaseModel):
    resolution_desc: str
    resolution_image: Optional[str] = None # Base64 

class SOSCreate(BaseModel):
    location: str
    user_id: int

class ChatRequest(BaseModel):
    query: str

@app.get("/api/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.put("/api/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.full_name:
        db_user.full_name = user_update.full_name
    if user_update.email:
        # Check if email is taken by another user
        existing_email = db.query(models.User).filter(models.User.email == user_update.email, models.User.id != user_id).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already in use")
        db_user.email = user_update.email
    
    if user_update.profile_image:
        try:
            # Handle image upload similarly to signup
            data_parts = user_update.profile_image.split(",")
            if len(data_parts) > 1:
                image_data = base64.b64decode(data_parts[1])
            else:
                image_data = base64.b64decode(data_parts[0])
            
            filename = f"{uuid.uuid4()}.png"
            file_path = os.path.join(UPLOAD_DIR, filename)
            
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            db_user.profile_image_path = f"/uploads/{filename}"
        except Exception as e:
            print(f"Error updating image: {e}")
            pass

    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/api/auth/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user.password)
    
    image_path = None
    if user.profile_image:
        try:
            # Simple base64 decode and save
            # Expecting "data:image/png;base64,....." or just base64
            data_parts = user.profile_image.split(",")
            if len(data_parts) > 1:
                image_data = base64.b64decode(data_parts[1])
            else:
                image_data = base64.b64decode(data_parts[0])
            
            filename = f"{uuid.uuid4()}.png"
            file_path = os.path.join(UPLOAD_DIR, filename)
            
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            image_path = f"/uploads/{filename}"
        except Exception as e:
            print(f"Error saving image: {e}")
            # Non-blocking error for now, just continue without image
            pass

    new_user = models.User(
        email=user.email, 
        full_name=user.full_name, 
        hashed_password=hashed_pwd,
        profile_image_path=image_path,
        role=user.role,
        department=user.department,
        state=user.state,
        district=user.district,
        sub_district=user.sub_district
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/auth/login")
def login(user: UserLogin, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Return simple user info (mock token mechanism)
    return {
        "message": "Login successful", 
        "user": {
            "id": db_user.id, 
            "email": db_user.email, 
            "full_name": db_user.full_name,
            "role": db_user.role,
            "department": db_user.department,
            "state": db_user.state,
            "district": db_user.district,
            "sub_district": db_user.sub_district,
            "profile_image_path": db_user.profile_image_path
        }
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    response = chat_with_rag(request.query)
    return {"reply": response}

@app.post("/api/reports")
def create_report(report: ReportCreate, db: Session = Depends(database.get_db)):
    # Convert tags list to string for storage
    tags_str = ",".join(report.tags)
    
    image_path = None
    if report.image:
        try:
            data_parts = report.image.split(",")
            if len(data_parts) > 1:
                image_data = base64.b64decode(data_parts[1])
            else:
                image_data = base64.b64decode(data_parts[0])
            
            filename = f"report_{uuid.uuid4()}.png"
            file_path = os.path.join(UPLOAD_DIR, filename)
            
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            image_path = f"/uploads/{filename}"
        except Exception as e:
            print(f"Error saving report image: {e}")
            pass

    new_report = models.Report(
        title=report.title,
        description=report.description,
        location=report.location,
        image_path=image_path,
        tags=tags_str,
        user_id=report.user_id
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return {"status": "Report Created", "id": new_report.id}

class CommentCreate(BaseModel):
    text: str
    user_id: int

class CommentOut(BaseModel):
    id: int
    text: str
    created_at: datetime.datetime
    user_name: str

    class Config:
        from_attributes = True

class ReportOut(BaseModel):
    id: int
    title: str
    description: str
    location: str
    image_path: Optional[str] = None
    tags: List[str]
    status: str
    created_at: datetime.datetime
    owner: str
    resolution_desc: Optional[str] = None
    resolution_image_path: Optional[str] = None
    resolved_at: Optional[datetime.datetime] = None
    votes: int
    comments: List[CommentOut] = []

    class Config:
        from_attributes = True

# ... (Previous code)

@app.get("/api/reports", response_model=List[ReportOut])
def get_reports(db: Session = Depends(database.get_db)):
    reports = db.query(models.Report).all()
    # Manual mapping to match Pydantic model structure if needed, or rely on ORM
    # Because we added relationships, we can try to let Pydantic handle it, 
    # but we need to ensure the data shape matches.
    # The simplest way to match the previous list-of-dicts approach is to construct it:
    result = []
    for r in reports:
        comments_data = []
        for c in r.comments:
            comments_data.append({
                "id": c.id,
                "text": c.text,
                "created_at": c.created_at,
                "user_name": c.owner.full_name if c.owner else "Anonymous"
            })

        result.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "location": r.location,
            "image_path": r.image_path,
            "tags": r.tags.split(",") if r.tags else [],
            "status": r.status,
            "created_at": r.created_at,
            "owner": r.owner.full_name if r.owner else "Anonymous",
            "resolution_desc": r.resolution_desc,
            "resolution_image_path": r.resolution_image_path,
            "resolved_at": r.resolved_at,
            "votes": r.votes,
            "comments": comments_data
        })
    return result

@app.post("/api/reports/{report_id}/vote")
def vote_report(report_id: int, db: Session = Depends(database.get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.votes += 1
    db.commit()
    return {"votes": report.votes}

@app.post("/api/reports/{report_id}/comments")
def add_comment(report_id: int, comment: CommentCreate, db: Session = Depends(database.get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    new_comment = models.Comment(
        text=comment.text,
        user_id=comment.user_id,
        report_id=report_id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return {
        "id": new_comment.id,
        "text": new_comment.text,
        "created_at": new_comment.created_at,
        "user_name": new_comment.owner.full_name if new_comment.owner else "Anonymous"
    }

@app.put("/api/reports/{report_id}/resolve")
def resolve_report(report_id: int, resolution: ReportResolve, db: Session = Depends(database.get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.resolution_desc = resolution.resolution_desc
    report.status = "Resolved"
    report.resolved_at = datetime.datetime.utcnow()

    if resolution.resolution_image:
        try:
            data_parts = resolution.resolution_image.split(",")
            if len(data_parts) > 1:
                image_data = base64.b64decode(data_parts[1])
            else:
                image_data = base64.b64decode(data_parts[0])
            
            filename = f"resolved_{uuid.uuid4()}.png"
            file_path = os.path.join(UPLOAD_DIR, filename)
            
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            report.resolution_image_path = f"/uploads/{filename}"
        except Exception as e:
            print(f"Error saving resolution image: {e}")
            pass

    db.commit()
    db.refresh(report)
    return {"status": "Resolved"}

@app.post("/api/sos")
def trigger_sos(sos: SOSCreate, db: Session = Depends(database.get_db)):
    new_sos = models.SOSAlert(location=sos.location, user_id=sos.user_id)
    db.add(new_sos)
    db.commit()
    return {"status": "SOS Alert Sent", "location": sos.location}

@app.get("/api/news")
def get_news():
    rss_url = "https://news.google.com/rss/search?q=India+Civic+Rights&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    articles = []
    for entry in feed.entries[:10]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
            "source": entry.source.title if 'source' in entry else "Google News"
        })
    return articles
