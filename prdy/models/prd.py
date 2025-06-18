"""
Core PRD data models using Pydantic for validation and SQLAlchemy for persistence
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ProductType(str, Enum):
    """Product type classification for determining PRD complexity and questions"""
    LANDING_PAGE = "landing_page"
    MOBILE_APP = "mobile_app"
    WEB_APP = "web_app"
    DESKTOP_APP = "desktop_app"
    SAAS_PLATFORM = "saas_platform"
    ENTERPRISE_SOFTWARE = "enterprise_software"
    ECOMMERCE = "ecommerce"
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    FULL_BUSINESS = "full_business"


class IndustryType(str, Enum):
    """Industry classification for specialized requirements"""
    GENERAL = "general"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    ENTERTAINMENT = "entertainment"
    LOGISTICS = "logistics"
    REAL_ESTATE = "real_estate"
    GOVERNMENT = "government"


class ComplexityLevel(str, Enum):
    """Project complexity level determining PRD template and requirements depth"""
    SIMPLE = "simple"          # 1-2 weeks, < 5 features
    MODERATE = "moderate"      # 2-8 weeks, 5-15 features
    COMPLEX = "complex"        # 2-6 months, 15-50 features
    ENTERPRISE = "enterprise"  # 6+ months, 50+ features


class TaskStatus(str, Enum):
    """Task completion status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskDifficulty(str, Enum):
    """Task difficulty assessment"""
    TRIVIAL = "trivial"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


# SQLAlchemy Models
class PRDSession(Base):
    """Database model for PRD generation sessions"""
    __tablename__ = "prd_sessions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    product_type = Column(String(50), nullable=False)
    industry_type = Column(String(50), nullable=False)
    complexity_level = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="in_progress")
    completion_percentage = Column(Integer, default=0)
    data = Column(JSON)  # Stores the actual PRD content
    
    # Relationships
    tasks = relationship("Task", back_populates="session")


class Task(Base):
    """Database model for task tracking"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("prd_sessions.id"))
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    identifier = Column(String(50), unique=True, nullable=False)  # e.g., PRD-001
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default=TaskStatus.PENDING.value)
    difficulty = Column(String(50), default=TaskDifficulty.MEDIUM.value)
    priority = Column(String(50), default="medium")
    
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)
    dependencies = Column(JSON)  # List of task IDs this depends on
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    session = relationship("PRDSession", back_populates="tasks")
    subtasks = relationship("Task", backref="parent_task", remote_side=[id])


# Pydantic Models for API/Validation
class PersonaBase(BaseModel):
    """User persona definition"""
    name: str
    role: str
    goals: List[str]
    pain_points: List[str]
    technical_expertise: str
    demographics: Dict[str, Any] = Field(default_factory=dict)


class FeatureBase(BaseModel):
    """Feature specification"""
    name: str
    description: str
    priority: str  # high, medium, low
    complexity: ComplexityLevel
    acceptance_criteria: List[str]
    dependencies: List[str] = Field(default_factory=list)
    user_stories: List[str] = Field(default_factory=list)


class TechnicalRequirement(BaseModel):
    """Technical requirement specification"""
    category: str  # performance, security, scalability, etc.
    requirement: str
    measurable_criteria: str
    priority: str


class BusinessRequirement(BaseModel):
    """Business requirement specification"""
    category: str  # revenue, compliance, market, etc.
    requirement: str
    success_criteria: str
    stakeholder: str


class PRDContent(BaseModel):
    """Complete PRD content structure"""
    # Executive Summary
    project_name: str
    executive_summary: str
    product_type: ProductType
    industry_type: IndustryType
    complexity_level: ComplexityLevel
    
    # Business Context
    problem_statement: str
    target_market: str
    value_proposition: str
    success_metrics: List[str]
    business_requirements: List[BusinessRequirement] = Field(default_factory=list)
    
    # User Research
    personas: List[PersonaBase] = Field(default_factory=list)
    user_journey_maps: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Product Specification
    features: List[FeatureBase] = Field(default_factory=list)
    technical_requirements: List[TechnicalRequirement] = Field(default_factory=list)
    
    # Implementation
    architecture_overview: str = ""
    technology_stack: List[str] = Field(default_factory=list)
    integrations: List[str] = Field(default_factory=list)
    
    # Project Management
    timeline: Dict[str, str] = Field(default_factory=dict)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    risks: List[Dict[str, str]] = Field(default_factory=list)
    
    # Compliance & Legal
    compliance_requirements: List[str] = Field(default_factory=list)
    privacy_requirements: List[str] = Field(default_factory=list)
    security_requirements: List[str] = Field(default_factory=list)


class TaskCreate(BaseModel):
    """Model for creating new tasks"""
    identifier: str
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    difficulty: TaskDifficulty = TaskDifficulty.MEDIUM
    priority: str = "medium"
    estimated_hours: Optional[int] = None
    dependencies: List[str] = Field(default_factory=list)
    parent_task_id: Optional[int] = None


class PRDSessionCreate(BaseModel):
    """Model for creating new PRD sessions"""
    name: str
    product_type: ProductType
    industry_type: IndustryType = IndustryType.GENERAL
    complexity_level: ComplexityLevel = ComplexityLevel.MODERATE