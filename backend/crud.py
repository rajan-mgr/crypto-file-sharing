# backend/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Tuple, Optional, List

import models


# =================================================
# USERS
# =================================================

def get_user(db: Session, username: str) -> Optional[models.User]:
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()


# =================================================
# FILES
# =================================================

def get_user_files(db: Session, username: str) -> List[models.SharedFile]:
    """Return all files owned by or shared with the user"""
    return (
        db.query(models.SharedFile)
        .filter(
            or_(
                models.SharedFile.owner_username == username,
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
    """Return file and permission row for a specific user"""
    file = (
        db.query(models.SharedFile)
        .filter(models.SharedFile.file_id == file_id)
        .filter(
            or_(
                models.SharedFile.owner_username == username,
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
    """Used for owner-only operations (delete, revoke access)"""
    return (
        db.query(models.SharedFile)
        .filter(models.SharedFile.file_id == file_id)
        .first()
    )


def get_file_permission(
    db: Session,
    file_id: str,
    recipient: str
) -> Optional[models.FilePermission]:
    """Return permission row for a specific file/user"""
    return (
        db.query(models.FilePermission)
        .filter(
            models.FilePermission.file_id == file_id,
            models.FilePermission.recipient == recipient
        )
        .first()
    )