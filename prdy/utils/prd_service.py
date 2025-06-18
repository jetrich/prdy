"""
PRD Service - Core business logic for PRD generation and management
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from ..models.database import get_db_sync
from ..models.prd import (
    PRDSession, Task, PRDSessionCreate, PRDContent, TaskCreate,
    ProductType, IndustryType, ComplexityLevel, TaskStatus, TaskDifficulty
)


class PRDService:
    """Service class for PRD operations"""
    
    def __init__(self):
        self.db = get_db_sync()
    
    def create_session(self, session_data: PRDSessionCreate) -> PRDSession:
        """Create a new PRD session"""
        session = PRDSession(
            name=session_data.name,
            product_type=session_data.product_type.value,
            industry_type=session_data.industry_type.value,
            complexity_level=session_data.complexity_level.value,
            data={}
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Create initial tasks
        self._create_initial_tasks(session.id, session_data.complexity_level)
        
        return session
    
    def get_session(self, session_id: int) -> Optional[PRDSession]:
        """Get a PRD session by ID"""
        return self.db.query(PRDSession).filter(PRDSession.id == session_id).first()
    
    def list_sessions(self) -> List[PRDSession]:
        """List all PRD sessions"""
        return self.db.query(PRDSession).order_by(PRDSession.updated_at.desc()).all()
    
    def update_session_data(self, session_id: int, data: Dict[str, Any]) -> bool:
        """Update session data with interview answers"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Merge new data with existing data
        if session.data:
            session.data.update(data)
        else:
            session.data = data
        
        # Update completion percentage based on answered questions
        total_questions = self._count_expected_questions(session)
        answered_questions = len([v for v in data.values() if v is not None and v != ""])
        session.completion_percentage = min(100, int((answered_questions / total_questions) * 100))
        
        session.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def generate_prd_content(self, session_id: int) -> Optional[PRDContent]:
        """Generate PRD content from session data"""
        session = self.get_session(session_id)
        if not session or not session.data:
            return None
        
        # Extract data from session
        data = session.data
        
        # Create PRD content object
        prd_content = PRDContent(
            project_name=data.get("project_name", session.name),
            executive_summary=self._generate_executive_summary(session, data),
            product_type=ProductType(session.product_type),
            industry_type=IndustryType(session.industry_type),
            complexity_level=ComplexityLevel(session.complexity_level),
            problem_statement=data.get("problem_statement", ""),
            target_market=data.get("target_audience", ""),
            value_proposition=data.get("value_proposition", ""),
            success_metrics=self._parse_list_field(data.get("success_metrics", "")),
        )
        
        # Add business requirements
        prd_content.business_requirements = self._generate_business_requirements(data)
        
        # Add personas
        prd_content.personas = self._generate_personas(data)
        
        # Add features
        prd_content.features = self._generate_features(data)
        
        # Add technical requirements
        prd_content.technical_requirements = self._generate_technical_requirements(session, data)
        
        # Add compliance requirements
        prd_content.compliance_requirements = self._generate_compliance_requirements(session, data)
        
        # Add timeline and milestones
        prd_content.timeline = self._generate_timeline(session, data)
        prd_content.milestones = self._generate_milestones(session, data)
        
        # Save generated content back to session
        session.data["generated_prd"] = prd_content.dict()
        session.status = "generated"
        session.completion_percentage = 100
        self.db.commit()
        
        return prd_content
    
    def export_prd(self, session_id: int, format: str) -> Optional[str]:
        """Export PRD to specified format"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Get or generate PRD content
        if "generated_prd" in session.data:
            prd_content = PRDContent(**session.data["generated_prd"])
        else:
            prd_content = self.generate_prd_content(session_id)
            if not prd_content:
                return None
        
        # Create exports directory
        exports_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(exports_dir, exist_ok=True)
        
        # Generate filename
        safe_name = "".join(c for c in session.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.{format}"
        filepath = os.path.join(exports_dir, filename)
        
        # Export based on format
        if format == "markdown":
            self._export_markdown(prd_content, filepath)
        elif format == "text":
            self._export_text(prd_content, filepath)
        elif format == "pdf":
            self._export_pdf(prd_content, filepath)
        else:
            return None
        
        return filepath
    
    def get_session_tasks(self, session_id: int) -> List[Task]:
        """Get all tasks for a session"""
        return self.db.query(Task).filter(Task.session_id == session_id).all()
    
    def create_task(self, session_id: int, task_data: TaskCreate) -> Task:
        """Create a new task"""
        task = Task(
            session_id=session_id,
            identifier=task_data.identifier,
            title=task_data.title,
            description=task_data.description,
            status=task_data.status.value,
            difficulty=task_data.difficulty.value,
            priority=task_data.priority,
            estimated_hours=task_data.estimated_hours,
            dependencies=task_data.dependencies,
            parent_task_id=task_data.parent_task_id
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def update_task_status(self, task_id: int, status: TaskStatus) -> bool:
        """Update task status"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        task.status = status.value
        task.updated_at = datetime.utcnow()
        
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def delete_session(self, session_id: int) -> bool:
        """Delete a PRD session and all associated tasks"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Delete associated tasks first
        self.db.query(Task).filter(Task.session_id == session_id).delete()
        
        # Delete session
        self.db.delete(session)
        self.db.commit()
        
        return True
    
    def _create_initial_tasks(self, session_id: int, complexity: ComplexityLevel):
        """Create initial task structure for the session"""
        base_tasks = [
            TaskCreate(
                identifier=f"PRD-{session_id:03d}-001",
                title="Conduct comprehensive interview",
                description="Complete all required questions for PRD generation",
                difficulty=TaskDifficulty.EASY,
                priority="high",
                estimated_hours=2
            ),
            TaskCreate(
                identifier=f"PRD-{session_id:03d}-002", 
                title="Generate initial PRD content",
                description="Create comprehensive PRD document from interview data",
                difficulty=TaskDifficulty.MEDIUM,
                priority="high",
                estimated_hours=4,
                dependencies=[f"PRD-{session_id:03d}-001"]
            ),
            TaskCreate(
                identifier=f"PRD-{session_id:03d}-003",
                title="Review and refine PRD",
                description="Review generated PRD for completeness and accuracy",
                difficulty=TaskDifficulty.EASY,
                priority="medium",
                estimated_hours=2,
                dependencies=[f"PRD-{session_id:03d}-002"]
            )
        ]
        
        # Add complexity-specific tasks
        if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.ENTERPRISE]:
            base_tasks.extend([
                TaskCreate(
                    identifier=f"PRD-{session_id:03d}-004",
                    title="Create detailed technical specifications",
                    description="Develop comprehensive technical requirements and architecture",
                    difficulty=TaskDifficulty.HARD,
                    priority="high",
                    estimated_hours=8,
                    dependencies=[f"PRD-{session_id:03d}-002"]
                ),
                TaskCreate(
                    identifier=f"PRD-{session_id:03d}-005",
                    title="Develop compliance framework",
                    description="Create detailed compliance and regulatory requirements",
                    difficulty=TaskDifficulty.EXPERT,
                    priority="medium",
                    estimated_hours=6,
                    dependencies=[f"PRD-{session_id:03d}-002"]
                )
            ])
        
        # Create tasks in database
        for task_data in base_tasks:
            self.create_task(session_id, task_data)
    
    def _count_expected_questions(self, session: PRDSession) -> int:
        """Count expected number of questions for the session type"""
        # This is a simplified count - in real implementation would use QuestionEngine
        base_count = 10
        
        if session.complexity_level == ComplexityLevel.SIMPLE.value:
            return base_count
        elif session.complexity_level == ComplexityLevel.MODERATE.value:
            return base_count + 5
        elif session.complexity_level == ComplexityLevel.COMPLEX.value:
            return base_count + 15
        else:  # Enterprise
            return base_count + 25
    
    def _generate_executive_summary(self, session: PRDSession, data: Dict[str, Any]) -> str:
        """Generate executive summary from session data"""
        project_name = data.get("project_name", session.name)
        problem = data.get("problem_statement", "")
        value_prop = data.get("value_proposition", "")
        
        summary = f"{project_name} is a {session.product_type.replace('_', ' ')} solution "
        
        if problem:
            summary += f"that addresses {problem.lower()}. "
        
        if value_prop:
            summary += f"Our unique value proposition is {value_prop.lower()}. "
        
        # Add complexity and timeline context
        complexity_desc = {
            ComplexityLevel.SIMPLE.value: "a streamlined solution designed for rapid deployment",
            ComplexityLevel.MODERATE.value: "a comprehensive solution with standard features",
            ComplexityLevel.COMPLEX.value: "an advanced solution with sophisticated capabilities",
            ComplexityLevel.ENTERPRISE.value: "an enterprise-grade solution with comprehensive features"
        }
        
        summary += f"This is {complexity_desc.get(session.complexity_level, 'a solution')} "
        summary += f"targeted at the {session.industry_type.replace('_', ' ')} industry."
        
        return summary
    
    def _parse_list_field(self, field_value: str) -> List[str]:
        """Parse a string field into a list"""
        if not field_value:
            return []
        
        # Handle comma-separated, newline-separated, or bullet-point lists
        items = []
        for line in field_value.split('\n'):
            line = line.strip()
            if line:
                # Remove bullet points and numbers
                line = line.lstrip('•-*123456789. ')
                if ',' in line:
                    items.extend([item.strip() for item in line.split(',') if item.strip()])
                else:
                    items.append(line)
        
        return items
    
    def _generate_business_requirements(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate business requirements from interview data"""
        requirements = []
        
        if data.get("business_model"):
            requirements.append({
                "category": "revenue",
                "requirement": f"Implement {data['business_model'].lower()} business model",
                "success_criteria": "Revenue model successfully integrated and operational",
                "stakeholder": "Business Development"
            })
        
        if data.get("revenue_goals"):
            requirements.append({
                "category": "financial",
                "requirement": f"Achieve revenue targets: {data['revenue_goals']}",
                "success_criteria": "Meet or exceed stated revenue goals",
                "stakeholder": "Finance"
            })
        
        return requirements
    
    def _generate_personas(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate user personas from interview data"""
        personas = []
        
        primary_users = data.get("primary_users", "")
        if primary_users:
            personas.append({
                "name": "Primary User",
                "role": "End User",
                "goals": self._parse_list_field(data.get("user_journey", "")),
                "pain_points": self._parse_list_field(data.get("problem_statement", "")),
                "technical_expertise": "Varies",
                "demographics": {"description": primary_users}
            })
        
        return personas
    
    def _generate_features(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate feature list from interview data"""
        features = []
        
        key_features = data.get("key_features", "")
        if key_features:
            feature_list = self._parse_list_field(key_features)
            
            for i, feature in enumerate(feature_list):
                features.append({
                    "name": f"Feature {i+1}",
                    "description": feature,
                    "priority": "high" if i < 3 else "medium",
                    "complexity": "moderate",
                    "acceptance_criteria": [f"User can {feature.lower()}"],
                    "dependencies": [],
                    "user_stories": [f"As a user, I want to {feature.lower()}"]
                })
        
        return features
    
    def _generate_technical_requirements(self, session: PRDSession, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate technical requirements based on product type and data"""
        requirements = []
        
        # Add performance requirements
        requirements.append({
            "category": "performance",
            "requirement": "Page load time under 3 seconds",
            "measurable_criteria": "95% of pages load within 3 seconds",
            "priority": "high"
        })
        
        # Add security requirements
        requirements.append({
            "category": "security",
            "requirement": "Secure data transmission and storage",
            "measurable_criteria": "All data encrypted in transit and at rest",
            "priority": "high"
        })
        
        # Add product-specific requirements
        if session.product_type == ProductType.MOBILE_APP.value:
            if data.get("offline_functionality"):
                requirements.append({
                    "category": "functionality",
                    "requirement": "Offline functionality support",
                    "measurable_criteria": "Core features work without internet connection",
                    "priority": "medium"
                })
        
        return requirements
    
    def _generate_compliance_requirements(self, session: PRDSession, data: Dict[str, Any]) -> List[str]:
        """Generate compliance requirements based on industry"""
        requirements = []
        
        if session.industry_type == IndustryType.HEALTHCARE.value:
            requirements.extend([
                "HIPAA compliance for protected health information",
                "Patient data encryption and access controls",
                "Audit trail for all data access"
            ])
        
        elif session.industry_type == IndustryType.FINANCE.value:
            requirements.extend([
                "PCI DSS compliance for payment processing",
                "SOX compliance for financial reporting",
                "Know Your Customer (KYC) procedures"
            ])
        
        # Add GDPR for all international products
        requirements.append("GDPR compliance for EU users")
        
        return requirements
    
    def _generate_timeline(self, session: PRDSession, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate project timeline"""
        timeline_mapping = {
            "2-4 weeks": {"planning": "1 week", "development": "2-3 weeks", "testing": "1 week"},
            "1-3 months": {"planning": "2 weeks", "development": "6-10 weeks", "testing": "2 weeks"},
            "3-6 months": {"planning": "1 month", "development": "3-4 months", "testing": "1 month"},
            "6-12 months": {"planning": "2 months", "development": "6-8 months", "testing": "2 months"},
            "12+ months": {"planning": "3 months", "development": "9+ months", "testing": "3 months"}
        }
        
        selected_timeline = data.get("timeline", "3-6 months")
        return timeline_mapping.get(selected_timeline, timeline_mapping["3-6 months"])
    
    def _generate_milestones(self, session: PRDSession, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate project milestones"""
        milestones = [
            {"name": "Requirements Complete", "description": "All requirements gathered and documented"},
            {"name": "Design Complete", "description": "UI/UX design finalized and approved"},
            {"name": "Development Phase 1", "description": "Core features implemented"},
            {"name": "Testing Phase", "description": "Comprehensive testing completed"},
            {"name": "Launch", "description": "Product launched to production"}
        ]
        
        return milestones
    
    def _export_markdown(self, prd_content: PRDContent, filepath: str):
        """Export PRD as Markdown"""
        content = f"""# {prd_content.project_name}

## Executive Summary
{prd_content.executive_summary}

## Problem Statement
{prd_content.problem_statement}

## Target Market
{prd_content.target_market}

## Value Proposition
{prd_content.value_proposition}

## Success Metrics
{chr(10).join(f"- {metric}" for metric in prd_content.success_metrics)}

## Key Features
{chr(10).join(f"### {feature['name']}{chr(10)}{feature['description']}{chr(10)}" for feature in prd_content.features)}

## Technical Requirements
{chr(10).join(f"- **{req['category'].title()}**: {req['requirement']}" for req in prd_content.technical_requirements)}

## Timeline
{chr(10).join(f"- **{phase.title()}**: {duration}" for phase, duration in prd_content.timeline.items())}

## Compliance Requirements
{chr(10).join(f"- {req}" for req in prd_content.compliance_requirements)}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _export_text(self, prd_content: PRDContent, filepath: str):
        """Export PRD as plain text"""
        content = f"""{prd_content.project_name}
{'=' * len(prd_content.project_name)}

EXECUTIVE SUMMARY
{prd_content.executive_summary}

PROBLEM STATEMENT
{prd_content.problem_statement}

TARGET MARKET
{prd_content.target_market}

VALUE PROPOSITION
{prd_content.value_proposition}

SUCCESS METRICS
{chr(10).join(f"• {metric}" for metric in prd_content.success_metrics)}

KEY FEATURES
{chr(10).join(f"{feature['name']}: {feature['description']}" for feature in prd_content.features)}

TECHNICAL REQUIREMENTS
{chr(10).join(f"• {req['category'].upper()}: {req['requirement']}" for req in prd_content.technical_requirements)}

TIMELINE
{chr(10).join(f"• {phase.upper()}: {duration}" for phase, duration in prd_content.timeline.items())}

COMPLIANCE REQUIREMENTS
{chr(10).join(f"• {req}" for req in prd_content.compliance_requirements)}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _export_pdf(self, prd_content: PRDContent, filepath: str):
        """Export PRD as PDF using ReportLab"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                spaceAfter=30,
            )
            story.append(Paragraph(prd_content.project_name, title_style))
            story.append(Spacer(1, 12))
            
            # Sections
            sections = [
                ("Executive Summary", prd_content.executive_summary),
                ("Problem Statement", prd_content.problem_statement),
                ("Target Market", prd_content.target_market),
                ("Value Proposition", prd_content.value_proposition),
            ]
            
            for title, content in sections:
                story.append(Paragraph(title, styles['Heading2']))
                story.append(Paragraph(content, styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Success Metrics
            story.append(Paragraph("Success Metrics", styles['Heading2']))
            for metric in prd_content.success_metrics:
                story.append(Paragraph(f"• {metric}", styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Features
            story.append(Paragraph("Key Features", styles['Heading2']))
            for feature in prd_content.features:
                story.append(Paragraph(f"<b>{feature['name']}</b>", styles['Normal']))
                story.append(Paragraph(feature['description'], styles['Normal']))
                story.append(Spacer(1, 6))
            
            doc.build(story)
            
        except ImportError:
            # Fallback to text export if ReportLab not available
            self._export_text(prd_content, filepath.replace('.pdf', '.txt'))