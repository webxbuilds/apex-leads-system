from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Task, Lead, User
from backend.app.core.security import get_current_user
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/tasks", tags=["Tasks & Calendar"])

class TaskCreateSchema(BaseModel):
    title: str
    description: Optional[str] = ""
    due_date: datetime
    lead_id: Optional[int] = None
    assigned_to_id: Optional[int] = None

class TaskUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None  # Pending, Completed
    assigned_to_id: Optional[int] = None


@router.get("/")
def get_tasks(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    query = db.query(Task)
    
    # Filter by user if not admin
    if current_user.role != "Admin":
        query = query.filter(Task.assigned_to_id == current_user.id)
        
    if status:
        query = query.filter(Task.status == status)
        
    tasks = query.order_by(Task.due_date.asc()).all()
    
    results = []
    for task in tasks:
        lead = db.query(Lead).filter(Lead.id == task.lead_id).first() if task.lead_id else None
        assigned_user = db.query(User).filter(User.id == task.assigned_to_id).first() if task.assigned_to_id else None
        
        results.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "status": task.status,
            "lead_id": task.lead_id,
            "lead_name": lead.business_name if lead else None,
            "assigned_to_id": task.assigned_to_id,
            "assigned_to_name": assigned_user.full_name if assigned_user else None
        })
        
    return results


@router.post("/")
def create_task(payload: TaskCreateSchema, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    task = Task(
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        lead_id=payload.lead_id,
        assigned_to_id=payload.assigned_to_id or current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}")
def update_task(task_id: int, payload: TaskUpdateSchema, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
        
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    db.delete(task)
    db.commit()
    return {"status": "success", "message": f"Task {task_id} successfully deleted"}
