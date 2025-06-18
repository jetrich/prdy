# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PRDY is a comprehensive cross-platform application (GUI + CLI) that creates detailed Product Requirements Documents (PRDs) for projects ranging from simple landing pages to complex enterprise systems. The system uses an adaptive question engine, AI assistance, SQLite database for session management, and exports to multiple formats.

## Development Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install in development mode**:
   ```bash
   pip install -e .
   ```

3. **Run the application**:
   ```bash
   prdy --help    # CLI interface
   prdy           # GUI interface (default)
   ```

## Common Commands

### Development Commands
- `pip install -e .` - Install package in development mode
- `pip install -e ".[dev]"` - Install with development dependencies
- `pytest` - Run tests (when test suite is added)
- `black prd_generator/` - Format code
- `mypy prd_generator/` - Type checking

### CLI Commands
- `prdy new` - Create new PRD session
- `prdy list` - List all sessions
- `prdy status <id>` - Show session status
- `prdy interview <id>` - Continue interview
- `prdy generate <id>` - Generate PRD content
- `prdy export <id> <format>` - Export PRD (markdown/pdf/text)
- `prdy delete <id>` - Delete session
- `prdy ai setup` - Configure AI providers
- `prdy --gui` - Launch GUI interface

## Architecture

### Core Components

1. **Models** (`prdy/models/`):
   - `prd.py` - Pydantic/SQLAlchemy models for data validation and persistence
   - `database.py` - Database connection and session management

2. **Engines** (`prdy/engines/`):
   - `question_engine.py` - Dynamic question generation based on product type/industry/complexity

3. **Utils** (`prdy/utils/`):
   - `prd_service.py` - Core business logic for PRD operations
   - `ai_integration.py` - AI provider management (Claude Code, Ollama)
   - `environment_manager.py` - Automated AI environment setup
   - `settings_manager.py` - Cross-platform settings persistence
   - `state_detector.py` - System health and bootstrap detection
   - `logger.py` - Comprehensive logging system

4. **Interfaces**:
   - `cli.py` - Rich-based command line interface
   - `gui.py` - Cross-platform Flet GUI interface
   - `app_controller.py` - Application lifecycle management

### Database Schema

- **prd_sessions**: Stores project info, interview data, and generated content
- **tasks**: Task management with dependencies, status tracking, and unique identifiers

### Data Flow

1. User creates session via CLI → PRDSessionCreate → SQLAlchemy model
2. Question engine generates questions based on product type/industry/complexity
3. CLI conducts interactive interview → Saves answers to session.data JSON field
4. PRD service generates structured content → PRDContent pydantic model
5. Export system converts to markdown/PDF/text formats

## Key Classes and Functions

### Models (`prdy/models/prd.py`)
- `PRDSession` - SQLAlchemy model for sessions
- `Task` - SQLAlchemy model for task tracking
- `PRDContent` - Pydantic model for structured PRD data
- `ProductType`, `IndustryType`, `ComplexityLevel` - Enums for classification

### Question Engine (`prdy/engines/question_engine.py`)
- `QuestionEngine.get_questions_for_product()` - Returns appropriate questions
- `QuestionEngine.filter_questions_by_dependencies()` - Handles conditional logic

### PRD Service (`prdy/utils/prd_service.py`)
- `PRDService.create_session()` - Creates new PRD session
- `PRDService.generate_prd_content()` - Converts interview data to structured PRD
- `PRDService.export_prd()` - Handles multi-format export

### AI Integration (`prdy/utils/ai_integration.py`)
- `AIIntegration.setup_ai_provider()` - Configures Claude Code or Ollama
- `AIIntegration.analyze_prd_gaps()` - AI-powered gap analysis
- `AIIntegration.enhance_prd_content()` - AI content enhancement

### Application Controller (`prdy/app_controller.py`)
- `ApplicationController.start_application()` - Main application orchestration
- Bootstrap detection and automatic setup
- Process management and graceful shutdown

## Task Management System

All development work uses structured task management:

- **Unique Identifiers**: Format PRDY-XXX (e.g., PRDY-001, PRDY-002) 
- **Dependencies**: Tasks can depend on other tasks
- **Status Tracking**: pending → in_progress → completed/blocked
- **Difficulty Levels**: trivial, easy, medium, hard, expert
- **Time Tracking**: estimated_hours and actual_hours fields

### Current Task Status
The system automatically creates tasks for each session:
- Interview completion
- PRD generation  
- Review and refinement
- Technical specifications (for complex projects)
- Compliance framework (for regulated industries)

## Testing

Currently no test suite - this should be added with:
- Unit tests for question engine logic
- Integration tests for PRD generation
- CLI command testing
- Database operation testing

Recommended test structure:
```
tests/
├── test_models.py
├── test_question_engine.py  
├── test_prd_service.py
└── test_cli.py
```

## Future Development

### Phase 2: AI Integration
- Claude Code integration for analysis and suggestions
- Ollama support for local AI processing
- Gap analysis and automated improvements

### Phase 3: Web Interface  
- NextJS/React frontend
- Real-time collaboration features
- Enhanced visualization

### Phase 4: Enterprise Features
- Multi-user support
- Custom templates
- API integrations
- Advanced analytics

## Development Guidelines

- Use type hints throughout (mypy compatibility)
- Follow Pydantic models for data validation
- Maintain SQLAlchemy models for persistence
- Keep CLI interface rich and user-friendly
- All exports must be both human and machine readable
- Maintain task tracking for all development work
- Use PRDY prefix for all task identifiers
- Cross-platform compatibility is essential
- AI integration should be optional but seamless when available