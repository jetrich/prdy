"""
Command Line Interface for PRDY
"""

import click
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress
from typing import Dict, Any, Optional
from datetime import datetime

from .models.database import init_database, get_db_sync
from .models.prd import (
    PRDSession, Task, ProductType, IndustryType, ComplexityLevel, 
    PRDSessionCreate, PRDContent, TaskCreate, TaskStatus
)
from .engines.question_engine import QuestionEngine, QuestionType
from .utils.prd_service import PRDService
from .utils.ai_integration import AIIntegration, AIProvider
from .utils.environment_manager import EnvironmentManager

console = Console()


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def main(ctx):
    """PRDY - AI-powered Product Requirements Document Generator"""
    # Initialize database
    init_database()
    
    # Set up context for app controller integration
    if ctx.obj is None:
        ctx.obj = {}


@main.command()
def new():
    """Create a new PRD session"""
    console.print(Panel.fit("🚀 Welcome to PRDY", style="bold blue"))
    console.print("Let's create a comprehensive Product Requirements Document for your project.\n")
    
    # Get basic project information
    product_type = questionary.select(
        "What type of product are you building?",
        choices=[
            "Landing Page",
            "Mobile App", 
            "Web Application",
            "Desktop Application",
            "SaaS Platform",
            "Enterprise Software",
            "E-commerce Site",
            "FinTech Product",
            "HealthTech Product",
            "Full Business/Startup"
        ]
    ).ask()
    
    # Map display names to enum values
    product_type_map = {
        "Landing Page": ProductType.LANDING_PAGE,
        "Mobile App": ProductType.MOBILE_APP,
        "Web Application": ProductType.WEB_APP,
        "Desktop Application": ProductType.DESKTOP_APP,
        "SaaS Platform": ProductType.SAAS_PLATFORM,
        "Enterprise Software": ProductType.ENTERPRISE_SOFTWARE,
        "E-commerce Site": ProductType.ECOMMERCE,
        "FinTech Product": ProductType.FINTECH,
        "HealthTech Product": ProductType.HEALTHTECH,
        "Full Business/Startup": ProductType.FULL_BUSINESS
    }
    
    industry = questionary.select(
        "What industry are you in?",
        choices=[
            "General/Other",
            "Finance",
            "Healthcare", 
            "Education",
            "Retail",
            "Manufacturing",
            "Entertainment",
            "Logistics",
            "Real Estate",
            "Government"
        ]
    ).ask()
    
    industry_map = {
        "General/Other": IndustryType.GENERAL,
        "Finance": IndustryType.FINANCE,
        "Healthcare": IndustryType.HEALTHCARE,
        "Education": IndustryType.EDUCATION,
        "Retail": IndustryType.RETAIL,
        "Manufacturing": IndustryType.MANUFACTURING,
        "Entertainment": IndustryType.ENTERTAINMENT,
        "Logistics": IndustryType.LOGISTICS,
        "Real Estate": IndustryType.REAL_ESTATE,
        "Government": IndustryType.GOVERNMENT
    }
    
    complexity = questionary.select(
        "What's the complexity level of your project?",
        choices=[
            "Simple (1-2 weeks, basic features)",
            "Moderate (2-8 weeks, standard features)",
            "Complex (2-6 months, advanced features)",
            "Enterprise (6+ months, comprehensive system)"
        ]
    ).ask()
    
    complexity_map = {
        "Simple (1-2 weeks, basic features)": ComplexityLevel.SIMPLE,
        "Moderate (2-8 weeks, standard features)": ComplexityLevel.MODERATE,
        "Complex (2-6 months, advanced features)": ComplexityLevel.COMPLEX,
        "Enterprise (6+ months, comprehensive system)": ComplexityLevel.ENTERPRISE
    }
    
    project_name = questionary.text(
        "What's the name of your project?",
        validate=lambda x: len(x.strip()) > 0
    ).ask()
    
    # Create PRD session
    session_data = PRDSessionCreate(
        name=project_name,
        product_type=product_type_map[product_type],
        industry_type=industry_map[industry],
        complexity_level=complexity_map[complexity]
    )
    
    # Initialize PRD service
    prd_service = PRDService()
    session = prd_service.create_session(session_data)
    
    console.print(f"\n✅ Created new PRD session: {project_name}")
    console.print(f"📋 Session ID: {session.id}")
    console.print(f"🎯 Product Type: {product_type}")
    console.print(f"🏢 Industry: {industry}")
    console.print(f"📊 Complexity: {complexity}")
    
    # Start the interview process
    if questionary.confirm("\nWould you like to start the PRD interview now?").ask():
        conduct_interview(session.id)


def conduct_interview(session_id: int):
    """Conduct the PRD interview for a session"""
    prd_service = PRDService()
    session = prd_service.get_session(session_id)
    
    if not session:
        console.print("❌ Session not found", style="red")
        return
    
    console.print(Panel.fit(f"📝 PRD Interview: {session.name}", style="bold green"))
    
    # Initialize question engine
    question_engine = QuestionEngine()
    
    # Convert string values back to enums
    product_type = ProductType(session.product_type)
    industry_type = IndustryType(session.industry_type)
    complexity_level = ComplexityLevel(session.complexity_level)
    
    questions = question_engine.get_questions_for_product(
        product_type,
        industry_type, 
        complexity_level
    )
    
    answers = {}
    
    with Progress() as progress:
        task = progress.add_task("[green]Answering questions...", total=len(questions))
        
        for question in questions:
            # Filter questions based on dependencies
            filtered_questions = question_engine.filter_questions_by_dependencies(
                [question], answers
            )
            
            if not filtered_questions:
                progress.advance(task)
                continue
            
            q = filtered_questions[0]
            
            # Display help text if available
            if q.help_text:
                console.print(f"💡 {q.help_text}", style="dim")
            
            # Ask question based on type
            if q.type == QuestionType.TEXT:
                answer = questionary.text(
                    q.question,
                    default=str(q.default) if q.default else ""
                ).ask()
            
            elif q.type == QuestionType.CHOICE:
                answer = questionary.select(
                    q.question,
                    choices=q.choices,
                    default=q.default if q.default in q.choices else None
                ).ask()
            
            elif q.type == QuestionType.MULTISELECT:
                answer = questionary.checkbox(
                    q.question,
                    choices=q.choices
                ).ask()
            
            elif q.type == QuestionType.CONFIRM:
                answer = questionary.confirm(
                    q.question,
                    default=q.default if q.default is not None else True
                ).ask()
            
            elif q.type == QuestionType.INTEGER:
                while True:
                    try:
                        answer = questionary.text(
                            q.question,
                            default=str(q.default) if q.default else ""
                        ).ask()
                        answer = int(answer)
                        break
                    except ValueError:
                        console.print("❌ Please enter a valid number", style="red")
            
            else:
                answer = questionary.text(q.question).ask()
            
            answers[q.id] = answer
            progress.advance(task)
    
    # Save answers to session
    prd_service.update_session_data(session_id, answers)
    
    console.print("\n✅ Interview completed!", style="green")
    console.print(f"💾 Answers saved to session {session_id}")
    
    # Ask if user wants to generate PRD
    if questionary.confirm("Would you like to generate the PRD now?").ask():
        generate_prd(session_id)


@main.command()
@click.argument('session_id', type=int)
def interview(session_id):
    """Continue or restart interview for a session"""
    conduct_interview(session_id)


@main.command()
@click.argument('session_id', type=int)
def generate(session_id):
    """Generate PRD for a session"""
    generate_prd(session_id)


def generate_prd(session_id: int):
    """Generate PRD document for a session"""
    prd_service = PRDService()
    session = prd_service.get_session(session_id)
    
    if not session:
        console.print("❌ Session not found", style="red")
        return
    
    console.print(Panel.fit(f"📄 Generating PRD: {session.name}", style="bold blue"))
    
    # Generate PRD content
    with console.status("🤖 Analyzing responses and generating PRD..."):
        prd_content = prd_service.generate_prd_content(session_id)
    
    if prd_content:
        console.print("✅ PRD generated successfully!", style="green")
        
        # Ask for export format
        export_format = questionary.select(
            "How would you like to export the PRD?",
            choices=["Markdown", "PDF", "Text", "View in terminal"]
        ).ask()
        
        if export_format == "View in terminal":
            display_prd_summary(prd_content)
        else:
            export_prd(session_id, export_format.lower())
    else:
        console.print("❌ Failed to generate PRD", style="red")


def display_prd_summary(prd_content: PRDContent):
    """Display PRD summary in terminal"""
    console.print(Panel.fit(f"📋 {prd_content.project_name}", style="bold blue"))
    
    # Executive Summary
    console.print("\n[bold]Executive Summary[/bold]")
    console.print(prd_content.executive_summary)
    
    # Problem Statement
    console.print("\n[bold]Problem Statement[/bold]")
    console.print(prd_content.problem_statement)
    
    # Features
    if prd_content.features:
        console.print("\n[bold]Key Features[/bold]")
        for i, feature in enumerate(prd_content.features[:5], 1):
            console.print(f"{i}. {feature.name}: {feature.description}")
    
    # Success Metrics
    if prd_content.success_metrics:
        console.print("\n[bold]Success Metrics[/bold]")
        for metric in prd_content.success_metrics:
            console.print(f"• {metric}")


@main.command()
@click.argument('session_id', type=int)
@click.argument('format', type=click.Choice(['markdown', 'pdf', 'text']))
def export(session_id, format):
    """Export PRD in specified format"""
    export_prd(session_id, format)


def export_prd(session_id: int, format: str):
    """Export PRD to file"""
    prd_service = PRDService()
    filename = prd_service.export_prd(session_id, format)
    
    if filename:
        console.print(f"✅ PRD exported to: {filename}", style="green")
    else:
        console.print("❌ Failed to export PRD", style="red")


@main.command()
def list():
    """List all PRD sessions"""
    prd_service = PRDService()
    sessions = prd_service.list_sessions()
    
    if not sessions:
        console.print("No PRD sessions found. Use 'prd new' to create one.", style="yellow")
        return
    
    table = Table(title="PRD Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Product Type", style="blue")
    table.add_column("Industry", style="magenta")
    table.add_column("Status", style="yellow")
    table.add_column("Created", style="dim")
    
    for session in sessions:
        table.add_row(
            str(session.id),
            session.name,
            session.product_type.replace('_', ' ').title(),
            session.industry_type.replace('_', ' ').title(),
            session.status,
            session.created_at.strftime("%Y-%m-%d")
        )
    
    console.print(table)


@main.command()
@click.argument('session_id', type=int)
def status(session_id):
    """Show status of a PRD session"""
    prd_service = PRDService()
    session = prd_service.get_session(session_id)
    
    if not session:
        console.print("❌ Session not found", style="red")
        return
    
    # Display session info
    console.print(Panel.fit(f"📊 Session Status: {session.name}", style="bold blue"))
    console.print(f"🆔 ID: {session.id}")
    console.print(f"🎯 Product Type: {session.product_type.replace('_', ' ').title()}")
    console.print(f"🏢 Industry: {session.industry_type.replace('_', ' ').title()}")
    console.print(f"📊 Complexity: {session.complexity_level.replace('_', ' ').title()}")
    console.print(f"✅ Status: {session.status}")
    console.print(f"📈 Completion: {session.completion_percentage}%")
    console.print(f"📅 Created: {session.created_at.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"🔄 Updated: {session.updated_at.strftime('%Y-%m-%d %H:%M')}")
    
    # Show tasks if any
    tasks = prd_service.get_session_tasks(session_id)
    if tasks:
        console.print("\n[bold]Tasks:[/bold]")
        for task in tasks:
            status_emoji = {
                TaskStatus.PENDING.value: "⏳",
                TaskStatus.IN_PROGRESS.value: "🔄", 
                TaskStatus.COMPLETED.value: "✅",
                TaskStatus.BLOCKED.value: "🚫"
            }.get(task.status, "❓")
            
            console.print(f"{status_emoji} {task.identifier}: {task.title}")


@main.command()
@click.argument('session_id', type=int)
def delete(session_id):
    """Delete a PRD session"""
    prd_service = PRDService()
    session = prd_service.get_session(session_id)
    
    if not session:
        console.print("❌ Session not found", style="red")
        return
    
    if questionary.confirm(f"Are you sure you want to delete session '{session.name}'?").ask():
        prd_service.delete_session(session_id)
        console.print(f"✅ Session {session_id} deleted", style="green")
    else:
        console.print("❌ Deletion cancelled", style="yellow")


@main.group()
def ai():
    """AI provider management commands"""
    pass


@ai.command()
def setup():
    """Set up AI environment (Claude Code or Ollama)"""
    console.print(Panel.fit("🤖 AI Environment Setup", style="bold blue"))
    
    ai_integration = AIIntegration()
    capabilities = ai_integration.env_manager.detect_capabilities()
    
    # Show system capabilities
    console.print("\n[bold]System Capabilities:[/bold]")
    for cap, available in capabilities.items():
        status = "✅" if available else "❌"
        console.print(f"{status} {cap.replace('_', ' ').title()}: {available}")
    
    # Let user choose provider
    choices = []
    if capabilities["node_js"] and capabilities["npm"]:
        choices.append("Claude Code (recommended)")
    if capabilities["ollama"]:
        choices.append("Ollama (local)")
    if not choices:
        choices.append("None (basic functionality only)")
    
    if len(choices) == 1 and "None" in choices[0]:
        console.print("\n❌ No AI providers available.", style="red")
        console.print("💡 Install Node.js/npm for Claude Code or Ollama for local AI.", style="blue")
        return
    
    choice = questionary.select(
        "\nWhich AI provider would you like to set up?",
        choices=choices
    ).ask()
    
    if choice.startswith("Claude Code"):
        if ai_integration.setup_ai_provider(AIProvider.CLAUDE_CODE):
            console.print("✅ Claude Code environment ready!", style="green")
        else:
            console.print("❌ Failed to set up Claude Code", style="red")
    
    elif choice.startswith("Ollama"):
        if ai_integration.setup_ai_provider(AIProvider.OLLAMA):
            console.print("✅ Ollama environment ready!", style="green")
        else:
            console.print("❌ Failed to set up Ollama", style="red")


@ai.command()
def status():
    """Show AI provider status"""
    ai_integration = AIIntegration()
    status_info = ai_integration.get_provider_status()
    
    console.print(Panel.fit("🤖 AI Provider Status", style="bold blue"))
    
    console.print(f"\n[bold]Current Provider:[/bold] {status_info['current_provider']}")
    console.print(f"[bold]Current Environment:[/bold] {status_info['current_environment'] or 'None'}")
    
    if status_info['available_environments']:
        console.print("\n[bold]Available Environments:[/bold]")
        for env_name in status_info['available_environments']:
            env_info = status_info['environments'][env_name]
            console.print(f"  • {env_name} ({env_info['provider']})")
    
    console.print("\n[bold]System Capabilities:[/bold]")
    for cap, available in status_info['system_capabilities'].items():
        status = "✅" if available else "❌"
        console.print(f"  {status} {cap.replace('_', ' ').title()}")


@ai.command()
@click.argument('provider', type=click.Choice(['claude-code', 'ollama', 'none']))
def switch(provider):
    """Switch AI provider"""
    ai_integration = AIIntegration()
    
    if provider == 'none':
        ai_integration.current_provider = AIProvider.NONE
        console.print("✅ Switched to no AI provider", style="green")
        return
    
    provider_enum = AIProvider.CLAUDE_CODE if provider == 'claude-code' else AIProvider.OLLAMA
    
    if ai_integration.switch_provider(provider_enum):
        console.print(f"✅ Switched to {provider}", style="green")
    else:
        console.print(f"❌ Failed to switch to {provider}. Environment may not be set up.", style="red")
        console.print("💡 Run 'prd ai setup' first.", style="blue")


@ai.command()
def test():
    """Test current AI provider"""
    ai_integration = AIIntegration()
    
    if ai_integration.current_provider == AIProvider.NONE:
        console.print("❌ No AI provider configured", style="red")
        return
    
    console.print(f"🧪 Testing {ai_integration.current_provider.value}...")
    
    test_data = {
        "project_name": "Test Project",
        "problem_statement": "Need to test AI integration",
        "product_type": "web_app"
    }
    
    with console.status("Running AI test..."):
        response = ai_integration.analyze_prd_gaps(test_data)
    
    if response.success:
        console.print("✅ AI provider working!", style="green")
        console.print(f"Response preview: {response.content[:200]}...")
    else:
        console.print("❌ AI provider test failed", style="red")
        console.print(f"Error: {response.content}")


if __name__ == "__main__":
    main()