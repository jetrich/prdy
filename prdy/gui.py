"""
GUI Application for PRDY using Flet
Cross-platform desktop interface
"""

import flet as ft
import asyncio
import threading
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

from .utils.settings_manager import SettingsManager, UserSettings
from .utils.state_detector import StateDetector
from .utils.logger import get_logger
from .utils.environment_manager import EnvironmentManager
from .utils.ai_integration import AIIntegration, AIProvider
from .utils.prd_service import PRDService
from .engines.question_engine import QuestionEngine, QuestionType
from .models.prd import ProductType, IndustryType, ComplexityLevel

logger = get_logger("gui")


class PRDYGUI:
    """Main GUI application class"""
    
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.state_detector = StateDetector(self.settings_manager)
        self.env_manager = EnvironmentManager()
        self.ai_integration = AIIntegration()
        self.prd_service = PRDService()
        
        # GUI state
        self.page: Optional[ft.Page] = None
        self.current_view = "home"
        self.system_state: Dict[str, Any] = {}
        self.bootstrap_in_progress = False
        
        # Components
        self.status_bar = None
        self.navigation_rail = None
        self.content_area = None
        self.bootstrap_dialog = None
        
        logger.info("PRDY GUI initialized")
    
    def run(self):
        """Run the GUI application"""
        ft.app(target=self.main, assets_dir="assets", view=ft.AppView.FLET_APP)
    
    async def main(self, page: ft.Page):
        """Main application entry point"""
        self.page = page
        
        # Configure page
        page.title = "PRDY"
        page.theme_mode = ft.ThemeMode.LIGHT if self.settings_manager.settings.theme == "light" else ft.ThemeMode.DARK
        page.window_width = self.settings_manager.settings.window_width
        page.window_height = self.settings_manager.settings.window_height
        page.window_resizable = True
        page.padding = 0
        
        # Set up page layout
        await self._setup_page_layout()
        
        # Check system state
        await self._check_system_state()
        
        # Handle first run
        if self.settings_manager.settings.first_run:
            await self._show_welcome_dialog()
        
        logger.info("GUI application started")
    
    async def _setup_page_layout(self):
        """Set up the main page layout"""
        # Status bar
        self.status_bar = ft.Container(
            content=ft.Row([
                ft.Text("Ready", size=12),
                ft.Container(expand=True),
                ft.Text("PRDY v0.1.0", size=12, color=ft.colors.GREY_600)
            ]),
            bgcolor=ft.colors.GREY_200,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            height=30
        )
        
        # Navigation rail
        self.navigation_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=160,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.HOME_OUTLINED,
                    selected_icon=ft.icons.HOME,
                    label="Home"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ADD_CIRCLE_OUTLINE,
                    selected_icon=ft.icons.ADD_CIRCLE,
                    label="New PRD"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.LIST_OUTLINED,
                    selected_icon=ft.icons.LIST,
                    label="Sessions"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SMART_TOY_OUTLINED,
                    selected_icon=ft.icons.SMART_TOY,
                    label="AI Setup"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_OUTLINED,
                    selected_icon=ft.icons.SETTINGS,
                    label="Settings"
                ),
            ],
            on_change=self._on_navigation_change
        )
        
        # Content area
        self.content_area = ft.Container(
            expand=True,
            padding=20
        )
        
        # Main layout
        main_row = ft.Row([
            self.navigation_rail,
            ft.VerticalDivider(width=1),
            self.content_area
        ], expand=True)
        
        # Add to page
        self.page.add(
            ft.Column([
                main_row,
                self.status_bar
            ], expand=True)
        )
        
        # Load initial view
        await self._load_home_view()
    
    async def _check_system_state(self):
        """Check and update system state"""
        self._update_status("Checking system state...")
        
        # Run state detection in background
        def check_state():
            self.system_state = self.state_detector.get_complete_system_state()
        
        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=check_state)
        thread.start()
        thread.join(timeout=10)  # 10 second timeout
        
        if thread.is_alive():
            logger.warning("System state check timed out")
            self._update_status("System state check timed out")
        else:
            bootstrap_status = self.system_state.get('bootstrap_status', {})
            if not bootstrap_status.get('is_ready', False):
                if self.settings_manager.settings.auto_bootstrap:
                    await self._show_bootstrap_dialog()
                else:
                    self._update_status("System needs setup")
            else:
                self._update_status("Ready")
    
    async def _show_welcome_dialog(self):
        """Show welcome dialog for first-time users"""
        def close_welcome(e):
            self.settings_manager.mark_first_run_complete()
            welcome_dialog.open = False
            self.page.update()
        
        welcome_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Welcome to PRDY!"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Thank you for installing PRDY."),
                    ft.Text(""),
                    ft.Text("This tool will help you create comprehensive Product Requirements Documents for any type of project."),
                    ft.Text(""),
                    ft.Text("Features:"),
                    ft.Text("• Adaptive question engine"),
                    ft.Text("• AI-powered analysis and suggestions"),
                    ft.Text("• Multiple export formats"),
                    ft.Text("• Comprehensive task tracking"),
                    ft.Text(""),
                    ft.Text("Let's get started by checking your system setup."),
                ], width=400),
            ),
            actions=[
                ft.TextButton("Get Started", on_click=close_welcome)
            ]
        )
        
        self.page.dialog = welcome_dialog
        welcome_dialog.open = True
        self.page.update()
    
    async def _show_bootstrap_dialog(self):
        """Show bootstrap dialog"""
        if self.bootstrap_in_progress:
            return
        
        self.bootstrap_in_progress = True
        
        progress_bar = ft.ProgressBar(width=400)
        status_text = ft.Text("Preparing to set up your system...", size=14)
        log_text = ft.Text("", size=12, color=ft.colors.GREY_600)
        
        def close_bootstrap(e):
            self.bootstrap_dialog.open = False
            self.bootstrap_in_progress = False
            self.page.update()
        
        def start_bootstrap(e):
            asyncio.create_task(self._run_bootstrap(progress_bar, status_text, log_text))
        
        self.bootstrap_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("System Setup Required"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Your system needs to be set up before using PRDY."),
                    ft.Text(""),
                    ft.Text("This will:"),
                    ft.Text("• Install required dependencies"),
                    ft.Text("• Set up AI environments (Claude Code/Ollama)"),
                    ft.Text("• Initialize the database"),
                    ft.Text("• Configure default settings"),
                    ft.Text(""),
                    status_text,
                    progress_bar,
                    ft.Container(height=10),
                    log_text
                ], width=500),
            ),
            actions=[
                ft.TextButton("Setup Now", on_click=start_bootstrap),
                ft.TextButton("Skip", on_click=close_bootstrap)
            ]
        )
        
        self.page.dialog = self.bootstrap_dialog
        self.bootstrap_dialog.open = True
        self.page.update()
    
    async def _run_bootstrap(self, progress_bar, status_text, log_text):
        """Run the bootstrap process"""
        steps = [
            ("Checking dependencies", self._bootstrap_check_dependencies),
            ("Setting up AI environments", self._bootstrap_setup_ai),
            ("Initializing database", self._bootstrap_init_database),
            ("Configuring settings", self._bootstrap_configure_settings),
            ("Validating setup", self._bootstrap_validate)
        ]
        
        for i, (step_name, step_func) in enumerate(steps):
            progress = (i / len(steps))
            progress_bar.value = progress
            status_text.value = f"{step_name}..."
            log_text.value = f"Step {i+1}/{len(steps)}: {step_name}"
            self.page.update()
            
            try:
                success = await step_func()
                if not success:
                    status_text.value = f"Failed: {step_name}"
                    log_text.value = f"Bootstrap failed at step: {step_name}"
                    self.page.update()
                    return
            except Exception as e:
                logger.error(f"Bootstrap step failed: {step_name}", exception=e)
                status_text.value = f"Error: {step_name}"
                log_text.value = f"Error in {step_name}: {str(e)}"
                self.page.update()
                return
            
            await asyncio.sleep(0.5)  # Brief pause for UI updates
        
        progress_bar.value = 1.0
        status_text.value = "Setup completed successfully!"
        log_text.value = "Your system is ready to use."
        self.page.update()
        
        # Close dialog after 2 seconds
        await asyncio.sleep(2)
        self.bootstrap_dialog.open = False
        self.bootstrap_in_progress = False
        self.page.update()
        
        # Refresh system state
        await self._check_system_state()
    
    async def _bootstrap_check_dependencies(self) -> bool:
        """Bootstrap step: Check dependencies"""
        deps = self.state_detector._check_dependencies()
        return deps['all_installed']
    
    async def _bootstrap_setup_ai(self) -> bool:
        """Bootstrap step: Set up AI environments"""
        try:
            # Try to set up Claude Code if Node.js is available
            tools = self.state_detector._check_system_tools()
            if tools['node']['available'] and tools['npm']['available']:
                self.ai_integration.setup_ai_provider(AIProvider.CLAUDE_CODE)
            
            # Try to set up Ollama if available
            if tools['ollama']['available']:
                self.ai_integration.setup_ai_provider(AIProvider.OLLAMA)
            
            return True
        except Exception as e:
            logger.error("AI setup failed", exception=e)
            return False
    
    async def _bootstrap_init_database(self) -> bool:
        """Bootstrap step: Initialize database"""
        try:
            from .models.database import init_database
            db_url = self.settings_manager.get_database_url()
            init_database(db_url)
            return True
        except Exception as e:
            logger.error("Database initialization failed", exception=e)
            return False
    
    async def _bootstrap_configure_settings(self) -> bool:
        """Bootstrap step: Configure settings"""
        try:
            # Set up default AI provider if available
            ai_status = self.state_detector._check_ai_providers()
            if ai_status['claude_code']['installed']:
                self.settings_manager.update_setting('ai_provider', 'claude-code')
            elif ai_status['ollama']['available']:
                self.settings_manager.update_setting('ai_provider', 'ollama')
            
            return True
        except Exception as e:
            logger.error("Settings configuration failed", exception=e)
            return False
    
    async def _bootstrap_validate(self) -> bool:
        """Bootstrap step: Validate setup"""
        try:
            health = self.state_detector.quick_health_check()
            return all(health.values())
        except Exception as e:
            logger.error("Validation failed", exception=e)
            return False
    
    def _update_status(self, message: str):
        """Update status bar message"""
        if self.status_bar and self.page:
            status_row = self.status_bar.content
            status_row.controls[0].value = message
            self.page.update()
    
    async def _on_navigation_change(self, e):
        """Handle navigation rail selection changes"""
        selected_index = e.control.selected_index
        
        views = ["home", "new_prd", "sessions", "ai_setup", "settings"]
        self.current_view = views[selected_index]
        
        view_loaders = {
            "home": self._load_home_view,
            "new_prd": self._load_new_prd_view,
            "sessions": self._load_sessions_view,
            "ai_setup": self._load_ai_setup_view,
            "settings": self._load_settings_view
        }
        
        await view_loaders[self.current_view]()
    
    async def _load_home_view(self):
        """Load the home view"""
        # System status cards
        status_cards = ft.Row([
            self._create_status_card("System", "Checking...", ft.colors.BLUE),
            self._create_status_card("AI Provider", "Checking...", ft.colors.GREEN),
            self._create_status_card("Database", "Checking...", ft.colors.ORANGE),
            self._create_status_card("Sessions", "Checking...", ft.colors.PURPLE)
        ])
        
        # Quick actions
        quick_actions = ft.Column([
            ft.Text("Quick Actions", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton(
                    "New PRD",
                    icon=ft.icons.ADD,
                    on_click=lambda e: self._navigate_to("new_prd")
                ),
                ft.ElevatedButton(
                    "View Sessions",
                    icon=ft.icons.LIST,
                    on_click=lambda e: self._navigate_to("sessions")
                ),
                ft.ElevatedButton(
                    "AI Setup",
                    icon=ft.icons.SMART_TOY,
                    on_click=lambda e: self._navigate_to("ai_setup")
                )
            ])
        ])
        
        # Recent sessions (placeholder)
        recent_sessions = ft.Column([
            ft.Text("Recent Sessions", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Text("No recent sessions", color=ft.colors.GREY_600)
        ])
        
        self.content_area.content = ft.Column([
            ft.Text("PRDY", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Create comprehensive Product Requirements Documents", size=16, color=ft.colors.GREY_600),
            ft.Container(height=20),
            status_cards,
            ft.Container(height=30),
            ft.Row([
                ft.Container(quick_actions, expand=1),
                ft.Container(recent_sessions, expand=1)
            ])
        ])
        
        self.page.update()
        
        # Update status cards asynchronously
        await self._update_status_cards(status_cards)
    
    def _create_status_card(self, title: str, value: str, color) -> ft.Container:
        """Create a status card"""
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                ft.Text(value, size=12)
            ]),
            bgcolor=color,
            padding=15,
            border_radius=8,
            expand=True
        )
    
    async def _update_status_cards(self, status_cards: ft.Row):
        """Update status cards with real data"""
        # This would update the cards with real system status
        # For now, just placeholder implementation
        await asyncio.sleep(1)
        
        cards = status_cards.controls
        cards[0].content.controls[1].value = "Ready"
        cards[1].content.controls[1].value = self.settings_manager.settings.ai_provider
        cards[2].content.controls[1].value = "Connected"
        cards[3].content.controls[1].value = "0 active"
        
        self.page.update()
    
    async def _load_new_prd_view(self):
        """Load the new PRD creation view"""
        # This would contain the PRD creation wizard
        self.content_area.content = ft.Column([
            ft.Text("Create New PRD", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.Text("PRD creation wizard coming soon...", size=16)
        ])
        self.page.update()
    
    async def _load_sessions_view(self):
        """Load the sessions view"""
        self.content_area.content = ft.Column([
            ft.Text("PRD Sessions", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.Text("Session management coming soon...", size=16)
        ])
        self.page.update()
    
    async def _load_ai_setup_view(self):
        """Load the AI setup view"""
        self.content_area.content = ft.Column([
            ft.Text("AI Provider Setup", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.Text("AI setup interface coming soon...", size=16)
        ])
        self.page.update()
    
    async def _load_settings_view(self):
        """Load the settings view"""
        self.content_area.content = ft.Column([
            ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.Text("Settings interface coming soon...", size=16)
        ])
        self.page.update()
    
    def _navigate_to(self, view: str):
        """Navigate to a specific view"""
        view_indices = {
            "home": 0,
            "new_prd": 1,
            "sessions": 2,
            "ai_setup": 3,
            "settings": 4
        }
        
        if view in view_indices:
            self.navigation_rail.selected_index = view_indices[view]
            self.current_view = view
            asyncio.create_task(self._on_navigation_change(type('obj', (object,), {'control': self.navigation_rail})))


def main():
    """Main entry point for GUI"""
    app = PRDYGUI()
    app.run()


if __name__ == "__main__":
    main()