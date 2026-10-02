from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

class TaskInput(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default='', max_length=1000)
    employee_id: int | None = None
    status: Literal['Pending','In Progress','Completed'] = 'Pending'
    priority: Literal['Low','Medium','High'] = 'Medium'
    deadline: date

class EmployeeInput(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=254)
    role: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=2, max_length=80)

class AnalyzeInput(BaseModel):
    period: Literal['week','month'] = 'week'
