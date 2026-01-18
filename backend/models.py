# backend/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary
from sqlalchemy.sql import func

from database import Base  # absolute import instead of relative


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    salt = Column(LargeBinary, nullable=False)              # for your existing encryption
    private_key_enc = Column(LargeBinary, nullable=False)
    public_key_pem = Column(Text, nullable=False)


class SharedFile(Base):
    __tablename__ = "shared_files"

    file_id = Column(String(36), primary_key=True, index=True)  # uuid string
    filename = Column(String(255), nullable=False)
    owner = Column(String(50), nullable=False)
    file_data = Column(LargeBinary, nullable=False)            # encrypted content
    signature = Column(LargeBinary, nullable=False)
    file_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class FilePermission(Base):
    __tablename__ = "file_permissions"

    id = Column(Integer, primary_key=True)
    file_id = Column(String(36), ForeignKey("shared_files.file_id"), nullable=False)
    recipient = Column(String(50), nullable=False)
    encrypted_sym_key = Column(LargeBinary, nullable=False)
