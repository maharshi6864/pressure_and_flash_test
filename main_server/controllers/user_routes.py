from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from models.db_models import User
from models.schemas import UserResponse, UserCreate, UserUpdate
from core.security import get_current_admin

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Admin-only: List all users in the system."""
    return db.query(User).order_by(User.id.asc()).all()

@router.post("", response_model=UserResponse)
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Admin-only: Create a new user."""
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_in.username}' is already registered."
        )

    new_user = User(
        name=user_in.name,
        username=user_in.username,
        password=user_in.password,
        hashed_password=user_in.password,
        role=user_in.role or "user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Admin-only: Retrieve user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Admin-only: Update username, name, password, or role."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_in.model_dump(exclude_unset=True)

    # If updating username, check uniqueness
    if "username" in update_data and update_data["username"] and update_data["username"] != user.username:
        existing = db.query(User).filter(User.username == update_data["username"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{update_data['username']}' is already in use."
            )
        user.username = update_data["username"]

    if "name" in update_data and update_data["name"] is not None:
        user.name = update_data["name"]

    if "password" in update_data and update_data["password"]:
        user.password = update_data["password"]
        user.hashed_password = update_data["password"]

    if "role" in update_data and update_data["role"]:
        user.role = update_data["role"]

    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Admin-only: Delete a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"status": "success", "message": f"User '{user.username}' deleted successfully"}
