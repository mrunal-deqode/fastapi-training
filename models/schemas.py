from pydantic import BaseModel, Field
from typing import Optional



class ContactInfo(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: Optional[str] = Field(default=None, min_length=10, max_length=10)
    
    
class ApplicationCreate(BaseModel):
    candidate_name:str = Field(min_length=2, max_length=30)
    job_title:str
    contact: ContactInfo
    years_of_experience: int

class ApplicationResponse(BaseModel):
    id:int
    candidate_name:str
    job_title:str
    contact:Optional[ContactInfo] = None
    years_of_experience:Optional[int] = None
    status: str


class ApplicationUpdate(BaseModel):
    candidate_name: Optional[str]= Field(default=None, min_length=2, max_length=30)
    job_title: Optional[str]= None
    contact: Optional[ContactInfo]= None
    years_of_experience: Optional[int]
    
class StatusUpdate(BaseModel):
    status: str
    
class JobCreate(BaseModel):
    title: str
    description: str
    job_type: str
    deadline: str
    
class JobResponse(BaseModel):
    id:int
    title:str
    description:str
    job_type:str
    deadline:str