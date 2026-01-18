# backend/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
import models
import schemas
from typing import Tuple, Optional, List


def get_user(db: Session, username: str) -> Optional[models.User]:
    """Get user by username - with debug output"""
    print(f"CRUD DEBUG: Searching for username: '{username}'")
    user = db.query(models.User).filter(models.User.username == username).first()
    print(f"CRUD DEBUG: User found: {user is not None}")
    if user:
        print(f"CRUD DEBUG: Found user: {user.username}, has public_key: {bool(user.public_key_pem)}")
    return user


def create_user(db: Session, username: str, password_hash: str, salt: bytes, priv_enc: bytes, pub_pem: str):
    user = models.User(
        username=username,
        password_hash=password_hash,
        salt=salt,
        private_key_enc=priv_enc,
        public_key_pem=pub_pem
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_files(db: Session, username: str) -> List[models.SharedFile]:
    return (
        db.query(models.SharedFile)
        .filter(
            or_(
                models.SharedFile.owner == username,
                models.SharedFile.file_id.in_(
                    db.query(models.FilePermission.file_id)
                    .filter(models.FilePermission.recipient == username)
                )
            )
        )
        .order_by(models.SharedFile.timestamp.desc())
        .all()
    )


def get_file_with_permission(
    db: Session,
    file_id: str,
    username: str
) -> Tuple[Optional[models.SharedFile], Optional[models.FilePermission]]:
    file = (
        db.query(models.SharedFile)
        .filter(models.SharedFile.file_id == file_id)
        .filter(
            or_(
                models.SharedFile.owner == username,
                models.SharedFile.file_id.in_(
                    db.query(models.FilePermission.file_id)
                    .filter(models.FilePermission.recipient == username)
                )
            )
        )
        .first()
    )

    if not file:
        return None, None

    permission = (
        db.query(models.FilePermission)
        .filter(
            models.FilePermission.file_id == file_id,
            models.FilePermission.recipient == username
        )
        .first()
    )

    return file, permission


def get_file_by_id(db: Session, file_id: str) -> Optional[models.SharedFile]:
    """Used by owner-only operations (delete, revoke)"""
    return db.query(models.SharedFile).filter(models.SharedFile.file_id == file_id).first()


def get_file_permission(db: Session, file_id: str, recipient: str) -> Optional[models.FilePermission]:
    return (
        db.query(models.FilePermission)
        .filter(
            models.FilePermission.file_id == file_id,
            models.FilePermission.recipient == recipient
        )
        .first()
    )