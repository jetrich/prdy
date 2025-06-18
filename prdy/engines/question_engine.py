"""
Dynamic question engine that adapts questions based on product type, industry, and complexity
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from ..models.prd import ProductType, IndustryType, ComplexityLevel


class QuestionType(str, Enum):
    """Types of questions for different input methods"""
    TEXT = "text"
    CHOICE = "choice" 
    MULTISELECT = "multiselect"
    CONFIRM = "confirm"
    INTEGER = "integer"
    FLOAT = "float"


@dataclass
class Question:
    """Individual question definition"""
    id: str
    question: str
    type: QuestionType
    required: bool = True
    choices: Optional[List[str]] = None
    default: Any = None
    help_text: Optional[str] = None
    depends_on: Optional[Dict[str, Any]] = None  # Conditional logic
    validation: Optional[str] = None  # Validation rules


class QuestionEngine:
    """Generates appropriate questions based on product characteristics"""
    
    def __init__(self):
        self.question_sets = self._initialize_question_sets()
    
    def _initialize_question_sets(self) -> Dict[str, Dict[str, List[Question]]]:
        """Initialize all question sets organized by category and product type"""
        return {
            "basic": self._get_basic_questions(),
            "business": self._get_business_questions(),
            "technical": self._get_technical_questions(),
            "user_research": self._get_user_research_questions(),
            "features": self._get_feature_questions(),
            "compliance": self._get_compliance_questions(),
            "project_management": self._get_project_management_questions()
        }
    
    def get_questions_for_product(
        self, 
        product_type: ProductType, 
        industry: IndustryType = IndustryType.GENERAL,
        complexity: ComplexityLevel = ComplexityLevel.MODERATE
    ) -> List[Question]:
        """Get complete question set for a specific product configuration"""
        questions = []
        
        # Always include basic questions
        questions.extend(self.question_sets["basic"]["all"])
        
        # Add business questions based on complexity
        if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.ENTERPRISE]:
            questions.extend(self.question_sets["business"]["detailed"])
        else:
            questions.extend(self.question_sets["business"]["basic"])
        
        # Add technical questions based on product type
        tech_questions = self.question_sets["technical"].get(product_type.value, [])
        questions.extend(tech_questions)
        
        # Add user research questions
        if complexity != ComplexityLevel.SIMPLE:
            questions.extend(self.question_sets["user_research"]["standard"])
        
        # Add feature questions based on product type
        feature_questions = self.question_sets["features"].get(product_type.value, [])
        questions.extend(feature_questions)
        
        # Add industry-specific compliance questions
        if industry != IndustryType.GENERAL:
            compliance_questions = self.question_sets["compliance"].get(industry.value, [])
            questions.extend(compliance_questions)
        
        # Add project management questions for complex projects
        if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.ENTERPRISE]:
            questions.extend(self.question_sets["project_management"]["detailed"])
        
        return questions
    
    def _get_basic_questions(self) -> Dict[str, List[Question]]:
        """Core questions for all products"""
        return {
            "all": [
                Question(
                    id="project_name",
                    question="What is the name of your project?",
                    type=QuestionType.TEXT,
                    help_text="Choose a clear, memorable name for your product"
                ),
                Question(
                    id="problem_statement",
                    question="What problem does this product solve?",
                    type=QuestionType.TEXT,
                    help_text="Describe the core problem or pain point your product addresses"
                ),
                Question(
                    id="target_audience",
                    question="Who is your primary target audience?",
                    type=QuestionType.TEXT,
                    help_text="Be specific about demographics, roles, or user characteristics"
                ),
                Question(
                    id="value_proposition",
                    question="What unique value does your product provide?",
                    type=QuestionType.TEXT,
                    help_text="What makes your solution better than alternatives?"
                ),
                Question(
                    id="key_features",
                    question="What are the 3-5 most important features?",
                    type=QuestionType.TEXT,
                    help_text="List the core features that deliver your value proposition"
                )
            ]
        }
    
    def _get_business_questions(self) -> Dict[str, List[Question]]:
        """Business-focused questions"""
        basic_questions = [
            Question(
                id="success_metrics",
                question="How will you measure success?",
                type=QuestionType.TEXT,
                help_text="Define specific, measurable success criteria"
            ),
            Question(
                id="timeline",
                question="What is your target launch timeline?",
                type=QuestionType.CHOICE,
                choices=["2-4 weeks", "1-3 months", "3-6 months", "6-12 months", "12+ months"]
            )
        ]
        
        detailed_questions = basic_questions + [
            Question(
                id="business_model",
                question="What is your business model?",
                type=QuestionType.CHOICE,
                choices=["Free", "One-time purchase", "Subscription", "Freemium", "Advertising", "Commission", "Other"]
            ),
            Question(
                id="revenue_goals",
                question="What are your revenue goals for year 1?",
                type=QuestionType.TEXT,
                help_text="Provide specific financial targets"
            ),
            Question(
                id="competitors",
                question="Who are your main competitors?",
                type=QuestionType.TEXT,
                help_text="List 3-5 direct or indirect competitors"
            ),
            Question(
                id="competitive_advantage", 
                question="What is your competitive advantage?",
                type=QuestionType.TEXT,
                help_text="What makes you different from competitors?"
            )
        ]
        
        return {
            "basic": basic_questions,
            "detailed": detailed_questions
        }
    
    def _get_technical_questions(self) -> Dict[str, List[Question]]:
        """Technical questions by product type"""
        return {
            ProductType.LANDING_PAGE.value: [
                Question(
                    id="hosting_preference",
                    question="Do you have a hosting preference?",
                    type=QuestionType.CHOICE,
                    choices=["Static hosting (Netlify/Vercel)", "WordPress", "Custom CMS", "No preference"],
                    required=False
                ),
                Question(
                    id="design_requirements",
                    question="Do you have specific design requirements?",
                    type=QuestionType.TEXT,
                    required=False,
                    help_text="Brand colors, style preferences, existing brand guidelines"
                )
            ],
            
            ProductType.MOBILE_APP.value: [
                Question(
                    id="platforms",
                    question="Which platforms do you want to support?",
                    type=QuestionType.MULTISELECT,
                    choices=["iOS", "Android", "Both"]
                ),
                Question(
                    id="native_vs_cross_platform",
                    question="Do you prefer native or cross-platform development?",
                    type=QuestionType.CHOICE,
                    choices=["Native (separate iOS/Android apps)", "Cross-platform (React Native/Flutter)", "No preference"]
                ),
                Question(
                    id="offline_functionality",
                    question="Does the app need to work offline?",
                    type=QuestionType.CONFIRM
                ),
                Question(
                    id="push_notifications",
                    question="Do you need push notifications?",
                    type=QuestionType.CONFIRM
                ),
                Question(
                    id="device_features",
                    question="Which device features do you need?",
                    type=QuestionType.MULTISELECT,
                    choices=["Camera", "GPS/Location", "Microphone", "Accelerometer", "Biometric auth", "None"],
                    required=False
                )
            ],
            
            ProductType.WEB_APP.value: [
                Question(
                    id="user_authentication",
                    question="Do you need user accounts and authentication?",
                    type=QuestionType.CONFIRM
                ),
                Question(
                    id="database_requirements",
                    question="What type of data will you store?",
                    type=QuestionType.TEXT,
                    help_text="User profiles, content, transactions, etc."
                ),
                Question(
                    id="third_party_integrations",
                    question="Do you need integrations with other services?",
                    type=QuestionType.TEXT,
                    required=False,
                    help_text="Payment processors, email services, social media, etc."
                ),
                Question(
                    id="expected_users",
                    question="How many users do you expect?",
                    type=QuestionType.CHOICE,
                    choices=["<100", "100-1000", "1000-10000", "10000+", "Unknown"]
                ),
                Question(
                    id="responsive_design",
                    question="Does it need to work well on mobile devices?",
                    type=QuestionType.CONFIRM,
                    default=True
                )
            ],
            
            ProductType.SAAS_PLATFORM.value: [
                Question(
                    id="multi_tenancy",
                    question="Do you need multi-tenant architecture?",
                    type=QuestionType.CONFIRM,
                    help_text="Multiple customers with isolated data"
                ),
                Question(
                    id="subscription_tiers",
                    question="How many subscription tiers will you offer?",
                    type=QuestionType.INTEGER,
                    default=3
                ),
                Question(
                    id="api_requirements",
                    question="Do you need to provide APIs for customers?",
                    type=QuestionType.CONFIRM
                ),
                Question(
                    id="admin_dashboard",
                    question="Do you need an admin dashboard?",
                    type=QuestionType.CONFIRM,
                    default=True
                ),
                Question(
                    id="analytics_requirements",
                    question="What analytics do you need to track?",
                    type=QuestionType.TEXT,
                    help_text="User behavior, feature usage, business metrics"
                )
            ]
        }
    
    def _get_user_research_questions(self) -> Dict[str, List[Question]]:
        """User research and persona questions"""
        return {
            "standard": [
                Question(
                    id="primary_users",
                    question="Describe your primary user personas",
                    type=QuestionType.TEXT,
                    help_text="Job titles, experience level, goals, pain points"
                ),
                Question(
                    id="user_journey",
                    question="Describe the typical user journey",
                    type=QuestionType.TEXT,
                    help_text="How do users discover, evaluate, and use your product?"
                ),
                Question(
                    id="user_research_done",
                    question="Have you conducted user research?",
                    type=QuestionType.CONFIRM
                ),
                Question(
                    id="user_feedback",
                    question="What feedback have you received from potential users?",
                    type=QuestionType.TEXT,
                    required=False,
                    depends_on={"user_research_done": True}
                )
            ]
        }
    
    def _get_feature_questions(self) -> Dict[str, List[Question]]:
        """Product-specific feature questions"""
        return {
            ProductType.ECOMMERCE.value: [
                Question(
                    id="payment_methods",
                    question="What payment methods do you want to support?",
                    type=QuestionType.MULTISELECT,
                    choices=["Credit/Debit Cards", "PayPal", "Apple Pay", "Google Pay", "Bank Transfer", "Cryptocurrency"]
                ),
                Question(
                    id="inventory_management",
                    question="Do you need inventory management?",
                    type=QuestionType.CONFIRM
                ),
                Question(
                    id="shipping_options",
                    question="What shipping options will you offer?",
                    type=QuestionType.TEXT,
                    help_text="Standard, express, international, pickup, etc."
                )
            ],
            
            ProductType.FINTECH.value: [
                Question(
                    id="financial_data_types",
                    question="What types of financial data will you handle?",
                    type=QuestionType.MULTISELECT,
                    choices=["Bank accounts", "Transactions", "Investments", "Credit scores", "Insurance", "Taxes"]
                ),
                Question(
                    id="regulatory_requirements",
                    question="Which financial regulations must you comply with?",
                    type=QuestionType.MULTISELECT,
                    choices=["PCI DSS", "SOX", "KYC", "AML", "GDPR", "CCPA", "Other"]
                )
            ]
        }
    
    def _get_compliance_questions(self) -> Dict[str, List[Question]]:
        """Industry-specific compliance questions"""
        return {
            IndustryType.HEALTHCARE.value: [
                Question(
                    id="hipaa_compliance",
                    question="Do you need HIPAA compliance?",
                    type=QuestionType.CONFIRM,
                    default=True
                ),
                Question(
                    id="medical_data_types",
                    question="What types of medical data will you handle?",
                    type=QuestionType.MULTISELECT,
                    choices=["Patient records", "Lab results", "Imaging", "Prescriptions", "Billing", "None"]
                )
            ],
            
            IndustryType.FINANCE.value: [
                Question(
                    id="financial_regulations",
                    question="Which financial regulations apply?",
                    type=QuestionType.MULTISELECT,
                    choices=["SOX", "PCI DSS", "FFIEC", "FINRA", "SEC", "Other"]
                ),
                Question(
                    id="audit_requirements",
                    question="Do you need audit trail capabilities?",
                    type=QuestionType.CONFIRM,
                    default=True
                )
            ]
        }
    
    def _get_project_management_questions(self) -> Dict[str, List[Question]]:
        """Project management and team questions"""
        return {
            "detailed": [
                Question(
                    id="team_size",
                    question="How large is your development team?",
                    type=QuestionType.INTEGER,
                    help_text="Number of developers, designers, etc."
                ),
                Question(
                    id="budget_range",
                    question="What is your budget range?",
                    type=QuestionType.CHOICE,
                    choices=["Under $10k", "$10k-$50k", "$50k-$100k", "$100k-$500k", "$500k+", "Prefer not to say"]
                ),
                Question(
                    id="existing_systems",
                    question="Do you have existing systems to integrate with?",
                    type=QuestionType.TEXT,
                    required=False,
                    help_text="CRM, ERP, databases, APIs, etc."
                ),
                Question(
                    id="maintenance_plan",
                    question="Who will maintain the system after launch?",
                    type=QuestionType.CHOICE,
                    choices=["Internal team", "External contractor", "Hybrid approach", "To be determined"]
                )
            ]
        }
    
    def filter_questions_by_dependencies(
        self, 
        questions: List[Question], 
        answers: Dict[str, Any]
    ) -> List[Question]:
        """Filter questions based on dependency logic"""
        filtered_questions = []
        
        for question in questions:
            if question.depends_on is None:
                filtered_questions.append(question)
                continue
            
            # Check if dependencies are satisfied
            dependencies_met = True
            for dep_key, dep_value in question.depends_on.items():
                if dep_key not in answers or answers[dep_key] != dep_value:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                filtered_questions.append(question)
        
        return filtered_questions