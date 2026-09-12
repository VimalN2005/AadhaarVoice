"""
SQLAlchemy ORM Models for AadhaarVoice.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), default="operator")  # admin, operator, auditor
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id = Column(Integer, primary_key=True, index=True)
    demo_vid = Column(String(12), unique=True, index=True, nullable=False)
    full_name_encrypted = Column(Text, nullable=False)
    phone_encrypted = Column(Text, nullable=True)
    gender = Column(String(16), default="unspecified")
    
    # Cryptographic biometric template data
    embedding_hash = Column(String(64), nullable=False)
    embedding_json = Column(Text, nullable=False)  # Serialized vector representation
    pitch_hz = Column(Float, default=150.0)
    sample_duration_seconds = Column(Float, default=0.0)
    
    # Metadata
    enrollment_status = Column(String(32), default="ACTIVE")  # ACTIVE, SUSPENDED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    verifications = relationship("VerificationLog", back_populates="profile", cascade="all, delete-orphan")


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("voice_profiles.id"), nullable=True)
    demo_vid = Column(String(12), index=True, nullable=False)
    
    # Biometric outcome
    verified = Column(Boolean, default=False)
    similarity_score = Column(Float, nullable=False)
    
    # Anti-spoofing & Deepfake outcome
    is_synthetic = Column(Boolean, default=False)
    deepfake_score = Column(Float, nullable=False)
    risk_level = Column(String(16), default="LOW")
    
    # Liveness check outcome
    challenge_passed = Column(Boolean, default=True)
    
    # Final state
    status = Column(String(32), nullable=False)  # AUTHENTICATED, REJECTED, SPOOF_DETECTED
    failure_reason = Column(String(255), nullable=True)
    
    # Client & session metadata
    ip_address = Column(String(64), default="127.0.0.1")
    client_user_agent = Column(String(255), default="unknown")
    
    # Tamper-evident ledger chaining
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    profile = relationship("VoiceProfile", back_populates="verifications")


class LivenessChallenge(Base):
    __tablename__ = "liveness_challenges"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(String(64), unique=True, index=True, nullable=False)
    demo_vid = Column(String(12), index=True, nullable=False)
    passphrase_text = Column(String(128), nullable=False)
    passphrase_phonetic = Column(String(128), nullable=False)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
