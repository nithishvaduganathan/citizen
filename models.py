from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    profile_image_path = Column(String, nullable=True)
    
    # New Fields
    role = Column(String, default="citizen") # citizen, authority
    department = Column(String, nullable=True) # Police, Municipal, etc.
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)
    sub_district = Column(String, nullable=True)

    reports = relationship("Report", back_populates="owner")
    sos_alerts = relationship("SOSAlert", back_populates="owner")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    location = Column(String)
    image_path = Column(String, nullable=True)
    tags = Column(String) # Comma separated tags
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    resolution_desc = Column(String, nullable=True)
    resolution_image_path = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # New Field
    votes = Column(Integer, default=0)

    owner = relationship("User", back_populates="reports")
    comments = relationship("Comment", back_populates="report")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    report_id = Column(Integer, ForeignKey("reports.id"))

    owner = relationship("User")
    report = relationship("Report", back_populates="comments")

class SOSAlert(Base):
    __tablename__ = "sos_alerts"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="sos_alerts")
