# PRDY

**AI-powered Product Requirements Document Generator** with **cross-platform GUI and CLI interfaces** that creates detailed, AI-consumable documentation for projects ranging from simple landing pages to complex enterprise systems and full business ventures.

## 🎯 **Self-Contained & Cross-Platform**

✅ **Windows, macOS, Linux** - Native GUI and CLI  
✅ **Automatic AI Setup** - Claude Code via npm, Ollama support  
✅ **One-Click Bootstrap** - Detects and sets up everything automatically  
✅ **Persistent Settings** - Retains user preferences between sessions  
✅ **Standalone Executables** - No Python installation required for end users

## Features

🎯 **Adaptive Question Engine**: Dynamic interview process that adapts questions based on product type, industry, and complexity level

📊 **Comprehensive Coverage**: Supports 10+ product types from landing pages to full business structures

🤖 **AI-Ready Output**: Generates machine-readable PRDs in multiple formats (Markdown, PDF, Text)

📈 **Task Management**: Built-in task tracking with unique identifiers, dependencies, and status management

💾 **Session Management**: Save, resume, and manage multiple PRD projects with SQLite storage

🏭 **Industry-Specific**: Specialized questions and compliance requirements for healthcare, finance, and other industries

## Product Types Supported

- Landing Pages
- Mobile Apps (iOS/Android)
- Web Applications 
- Desktop Applications
- SaaS Platforms
- Enterprise Software
- E-commerce Sites
- FinTech Products
- HealthTech Products
- Full Business/Startup Plans

## Installation

### 🚀 **One-Command Setup (Recommended)**

**Linux/macOS:**
```bash
git clone https://github.com/jetrich/prdy.git
cd prdy
./setup.sh
```

**Windows:**
```cmd
git clone https://github.com/jetrich/prdy.git
cd prdy
setup.bat
```

### 🐍 **Manual Virtual Environment Setup**
```bash
git clone https://github.com/jetrich/prdy.git
cd prdy

# Create and activate virtual environment
python3 -m venv prdy-env
source prdy-env/bin/activate  # On Windows: prdy-env\Scripts\activate

# Install dependencies and package
pip install -r requirements.txt
pip install -e .
```

### 🚀 **Alternative Installation Methods**

**Option 1: Using pipx (Isolated)**
```bash
pipx install git+https://github.com/jetrich/prdy.git
```

**Option 2: System-wide (Debian/Ubuntu)**
```bash
git clone https://github.com/jetrich/prdy.git
cd prdy
pip install -r requirements.txt --break-system-packages
pip install -e . --break-system-packages
```

**Option 3: Using uv (Fastest)**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -e .
```

### 🔧 **Installation Troubleshooting**

**Issue: `externally-managed-environment` error on Debian/Ubuntu**
```bash
# Solution 1: Use virtual environment (recommended)
python3 -m venv prdy-env
source prdy-env/bin/activate
pip install -r requirements.txt

# Solution 2: Use --break-system-packages flag
pip install -r requirements.txt --break-system-packages

# Solution 3: Use pipx for isolation
pipx install git+https://github.com/jetrich/prdy.git
```

**Issue: Permission denied errors**
```bash
# Use --user flag to install in user directory
pip install -r requirements.txt --user
pip install -e . --user
```

**Issue: Missing Python development headers**
```bash
# Ubuntu/Debian
sudo apt install python3-dev python3-venv

# CentOS/RHEL/Fedora  
sudo dnf install python3-devel python3-venv

# macOS (using Homebrew)
brew install python
```

**Issue: Corrupted virtual environment**
```bash
# Clean and reinstall
./clean.sh          # Remove old environment
./setup.sh          # Fresh installation
```

## Quick Start

### Create a New PRD

```bash
prdy new
```

This will launch an interactive session where you'll:
1. Select your product type
2. Choose your industry
3. Set complexity level
4. Complete a comprehensive interview
5. Generate your PRD

### List All PRD Sessions

```bash
prdy list
```

### Check Session Status

```bash
prdy status <session_id>
```

### Export a PRD

```bash
prdy export <session_id> <format>
# Formats: markdown, pdf, text
```

### Continue an Interview

```bash
prdy interview <session_id>
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `prdy new` | Create a new PRD session |
| `prdy list` | List all PRD sessions |
| `prdy status <id>` | Show session status and progress |
| `prdy interview <id>` | Continue or restart interview |
| `prdy generate <id>` | Generate PRD content |
| `prdy export <id> <format>` | Export PRD (markdown/pdf/text) |
| `prdy delete <id>` | Delete a PRD session |

## Project Structure

```
prdy/
├── models/          # Data models and database schema
│   ├── prd.py      # Core PRD models
│   └── database.py # Database management
├── engines/         # Question and processing engines
│   └── question_engine.py # Dynamic question generation
├── utils/          # Business logic and services
│   └── prd_service.py # Core PRD operations
├── templates/      # PRD templates (future)
├── exporters/      # Export functionality (future)
├── gui.py         # Cross-platform GUI interface
└── cli.py         # Command line interface
```

## Task Management Features

- **Unique Identifiers**: All tasks have unique IDs (e.g., PRD-001-001)
- **Dependency Tracking**: Tasks can depend on other tasks
- **Status Management**: Track progress with pending/in-progress/completed/blocked
- **Difficulty Assessment**: Rate tasks from trivial to expert level
- **Time Estimation**: Track estimated vs actual hours

## Database Schema

The system uses SQLite by default with two main tables:

- **prd_sessions**: Stores PRD project information and interview data
- **tasks**: Manages task tracking with relationships and dependencies

## Configuration

Create a `.env` file to customize settings:

```env
DATABASE_URL=sqlite:///./prdy.db
# or use PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/prdy
```

## Export Formats

### Markdown
Human-readable format with proper headings and structure

### PDF
Professional document format using ReportLab

### Text
Plain text format for simple consumption

## Development

### Setup Development Environment

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black prd_generator/
```

### Type Checking

```bash
mypy prd_generator/
```

## Future Enhancements

### Phase 2: AI Integration
- Integration with Claude Code for enhanced analysis
- Ollama support for local AI processing
- Automated gap analysis and suggestions

### Phase 3: Web Interface
- React/NextJS web application
- Real-time collaboration
- Advanced visualization

### Phase 4: Enterprise Features
- Team management
- Custom templates
- API integrations
- Advanced analytics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and feature requests, please use the GitHub issues tracker at https://github.com/jetrich/prdy/issues

---

*Built with PRDY - AI-powered Product Requirements Document Generator*