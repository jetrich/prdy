"""
Main entry point for PRDY
Handles both GUI and CLI modes
"""

import sys
import os
import argparse
from pathlib import Path

# Add current directory to path for relative imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from prdy.app_controller import ApplicationController
from prdy.utils.logger import get_logger

logger = get_logger("main")


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        prog='prdy',
        description='PRDY - AI-powered Product Requirements Document Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  prdy                    # Start GUI interface
  prdy --cli              # Start CLI interface
  prdy --gui              # Start GUI interface (explicit)
  prdy --bootstrap        # Force bootstrap process
  prdy --check            # Check system status
  prdy --version          # Show version
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--gui',
        action='store_true',
        help='Start GUI interface (default)'
    )
    mode_group.add_argument(
        '--cli',
        action='store_true',
        help='Start CLI interface'
    )
    
    # Utility commands
    parser.add_argument(
        '--bootstrap',
        action='store_true',
        help='Force bootstrap/setup process'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check system status and exit'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='PRDY 0.1.0'
    )
    
    # Configuration options
    parser.add_argument(
        '--config-dir',
        type=str,
        help='Override default configuration directory'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    parser.add_argument(
        '--no-auto-bootstrap',
        action='store_true',
        help='Disable automatic bootstrapping'
    )
    
    return parser


def check_system_status():
    """Check and display system status"""
    try:
        from prdy.utils.state_detector import StateDetector
        from prdy.utils.settings_manager import SettingsManager
        
        settings_manager = SettingsManager()
        state_detector = StateDetector(settings_manager)
        
        print("🔍 Checking PRDY system status...\n")
        
        # Get comprehensive system state
        system_state = state_detector.get_complete_system_state()
        
        # Display Python environment
        python_env = system_state.get('python_environment', {})
        print(f"🐍 Python Environment:")
        print(f"   Version: {python_env.get('version', 'Unknown')}")
        print(f"   Compatible: {'✅' if python_env.get('version_compatible', False) else '❌'}")
        print(f"   Virtual Environment: {'✅' if python_env.get('virtual_env', False) else '❌'}")
        print()
        
        # Display dependencies
        deps = system_state.get('dependencies', {})
        print(f"📦 Dependencies:")
        print(f"   Installed: {len(deps.get('installed', []))}/{len(deps.get('required', []))}")
        print(f"   All Required: {'✅' if deps.get('all_installed', False) else '❌'}")
        if deps.get('missing'):
            print(f"   Missing: {', '.join(deps['missing'])}")
        print()
        
        # Display system tools
        tools = system_state.get('system_tools', {})
        print(f"🔧 System Tools:")
        for tool, info in tools.items():
            if tool != 'summary':
                status = '✅' if info.get('available', False) else '❌'
                version = f" ({info.get('version', 'unknown')})" if info.get('version') else ""
                print(f"   {tool}: {status}{version}")
        print()
        
        # Display AI providers
        ai = system_state.get('ai_providers', {})
        print(f"🤖 AI Providers:")
        
        claude_code = ai.get('claude_code', {})
        status = '✅' if claude_code.get('installed', False) else '❌'
        working = '🟢' if claude_code.get('working', False) else '🔴'
        print(f"   Claude Code: {status} {working}")
        
        ollama = ai.get('ollama', {})
        status = '✅' if ollama.get('available', False) else '❌'
        running = '🟢' if ollama.get('running', False) else '🔴'
        print(f"   Ollama: {status} {running}")
        print()
        
        # Display database
        db = system_state.get('database', {})
        print(f"💾 Database:")
        print(f"   Initialized: {'✅' if db.get('initialized', False) else '❌'}")
        print(f"   Connection: {'✅' if db.get('connection_working', False) else '❌'}")
        if db.get('session_count') is not None:
            print(f"   Sessions: {db['session_count']}")
        print()
        
        # Display bootstrap status
        bootstrap = system_state.get('bootstrap_status', {})
        print(f"🚀 Bootstrap Status:")
        print(f"   Ready: {'✅' if bootstrap.get('is_ready', False) else '❌'}")
        
        missing = bootstrap.get('missing_components', [])
        if missing:
            print(f"   Missing: {', '.join(missing)}")
        
        recommendations = bootstrap.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        # Overall status
        overall_status = "✅ READY" if bootstrap.get('is_ready', False) else "❌ NEEDS SETUP"
        print(f"\n📊 Overall Status: {overall_status}")
        
        return bootstrap.get('is_ready', False)
        
    except Exception as e:
        logger.error("System status check failed", exception=e)
        print(f"❌ System status check failed: {e}")
        return False


def force_bootstrap():
    """Force the bootstrap process"""
    try:
        print("🚀 Starting PRDY bootstrap process...\n")
        
        app_controller = ApplicationController()
        
        # Disable auto-bootstrap setting temporarily
        original_setting = app_controller.settings_manager.settings.auto_bootstrap
        app_controller.settings_manager.update_setting('auto_bootstrap', True)
        
        try:
            success = app_controller._auto_bootstrap()
            
            if success:
                print("✅ Bootstrap completed successfully!")
                return True
            else:
                print("❌ Bootstrap failed. Check logs for details.")
                return False
                
        finally:
            # Restore original setting
            app_controller.settings_manager.update_setting('auto_bootstrap', original_setting)
            
    except Exception as e:
        logger.error("Forced bootstrap failed", exception=e)
        print(f"❌ Bootstrap failed: {e}")
        return False


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up logging level
    if args.log_level:
        from prdy.utils.logger import logger as main_logger
        main_logger.set_level(args.log_level)
    
    # Handle utility commands first
    if args.check:
        success = check_system_status()
        sys.exit(0 if success else 1)
    
    if args.bootstrap:
        success = force_bootstrap()
        sys.exit(0 if success else 1)
    
    # Determine interface mode
    if args.cli:
        mode = "cli"
    else:
        mode = "gui"  # Default to GUI
    
    # Update settings if specified
    try:
        app_controller = ApplicationController()
        
        if args.no_auto_bootstrap:
            app_controller.settings_manager.update_setting('auto_bootstrap', False)
        
        # Start the application
        logger.info(f"Starting PRDY in {mode} mode")
        
        success = app_controller.start_application(mode)
        
        if not success:
            logger.error("Application failed to start")
            print("❌ Application failed to start. Check logs for details.")
            
            # Offer to run system check
            try:
                response = input("\nWould you like to run a system check? (y/N): ")
                if response.lower().strip() == 'y':
                    check_system_status()
            except (EOFError, KeyboardInterrupt):
                pass
            
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nApplication interrupted.")
        sys.exit(0)
    except Exception as e:
        logger.critical("Unexpected error in main", exception=e)
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()