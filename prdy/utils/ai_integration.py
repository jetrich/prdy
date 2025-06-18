"""
AI Integration layer for PRD Generator
Supports both Claude Code and Ollama providers
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .environment_manager import EnvironmentManager, EnvironmentConfig


class AIProvider(str, Enum):
    """Supported AI providers"""
    CLAUDE_CODE = "claude-code"
    OLLAMA = "ollama"
    NONE = "none"


@dataclass
class AIResponse:
    """Standardized AI response format"""
    content: str
    success: bool
    provider: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AIIntegration:
    """Main AI integration class"""
    
    def __init__(self):
        self.env_manager = EnvironmentManager()
        self.current_provider = AIProvider.NONE
        self.current_environment = None
    
    def setup_ai_provider(self, provider: AIProvider, auto_install: bool = True) -> bool:
        """Set up and configure AI provider"""
        if provider == AIProvider.CLAUDE_CODE:
            return self._setup_claude_code(auto_install)
        elif provider == AIProvider.OLLAMA:
            return self._setup_ollama(auto_install)
        else:
            self.current_provider = AIProvider.NONE
            return True
    
    def _setup_claude_code(self, auto_install: bool = True) -> bool:
        """Set up Claude Code environment"""
        # Check if already configured
        env_config = self.env_manager.get_environment("claude-code")
        
        if env_config is None and auto_install:
            print("🚀 Setting up Claude Code environment...")
            if not self.env_manager.setup_claude_code_environment():
                return False
            env_config = self.env_manager.get_environment("claude-code")
        
        if env_config:
            self.current_provider = AIProvider.CLAUDE_CODE
            self.current_environment = "claude-code"
            return True
        
        return False
    
    def _setup_ollama(self, auto_install: bool = True) -> bool:
        """Set up Ollama environment"""
        # Check if already configured
        env_config = self.env_manager.get_environment("ollama")
        
        if env_config is None and auto_install:
            print("🚀 Setting up Ollama environment...")
            if not self.env_manager.setup_ollama_environment():
                return False
            env_config = self.env_manager.get_environment("ollama")
        
        if env_config:
            self.current_provider = AIProvider.OLLAMA
            self.current_environment = "ollama"
            return True
        
        return False
    
    def analyze_prd_gaps(self, session_data: Dict[str, Any]) -> AIResponse:
        """Analyze PRD data for gaps and suggestions"""
        if self.current_provider == AIProvider.NONE:
            return AIResponse(
                content="No AI provider configured. PRD generated with basic templates.",
                success=True,
                provider="none"
            )
        
        prompt = self._create_gap_analysis_prompt(session_data)
        
        if self.current_provider == AIProvider.CLAUDE_CODE:
            return self._query_claude_code(prompt)
        elif self.current_provider == AIProvider.OLLAMA:
            return self._query_ollama(prompt)
        
        return AIResponse(
            content="Unknown AI provider",
            success=False,
            provider=str(self.current_provider)
        )
    
    def enhance_prd_content(self, prd_content: Dict[str, Any]) -> AIResponse:
        """Enhance existing PRD content with AI suggestions"""
        if self.current_provider == AIProvider.NONE:
            return AIResponse(
                content="No enhancements applied - no AI provider configured.",
                success=True,
                provider="none"
            )
        
        prompt = self._create_enhancement_prompt(prd_content)
        
        if self.current_provider == AIProvider.CLAUDE_CODE:
            return self._query_claude_code(prompt)
        elif self.current_provider == AIProvider.OLLAMA:
            return self._query_ollama(prompt)
        
        return AIResponse(
            content="Unknown AI provider",
            success=False,
            provider=str(self.current_provider)
        )
    
    def suggest_technical_requirements(self, session_data: Dict[str, Any]) -> AIResponse:
        """Generate technical requirement suggestions"""
        if self.current_provider == AIProvider.NONE:
            return AIResponse(
                content="Basic technical requirements generated from templates.",
                success=True,
                provider="none"
            )
        
        prompt = self._create_technical_requirements_prompt(session_data)
        
        if self.current_provider == AIProvider.CLAUDE_CODE:
            return self._query_claude_code(prompt)
        elif self.current_provider == AIProvider.OLLAMA:
            return self._query_ollama(prompt)
        
        return AIResponse(
            content="Unknown AI provider",
            success=False,
            provider=str(self.current_provider)
        )
    
    def _create_gap_analysis_prompt(self, session_data: Dict[str, Any]) -> str:
        """Create prompt for gap analysis"""
        return f"""
Analyze the following PRD session data for completeness and suggest improvements:

SESSION DATA:
{json.dumps(session_data, indent=2)}

Please provide:
1. Identify any missing critical information
2. Suggest additional questions that should be asked
3. Recommend areas that need more detail
4. Flag potential risks or challenges
5. Suggest best practices for this type of project

Format your response as structured recommendations with clear action items.
"""
    
    def _create_enhancement_prompt(self, prd_content: Dict[str, Any]) -> str:
        """Create prompt for PRD enhancement"""
        return f"""
Review and enhance the following PRD content:

PRD CONTENT:
{json.dumps(prd_content, indent=2)}

Please provide:
1. Enhanced descriptions for unclear sections
2. Additional features or requirements that might be missing
3. More detailed acceptance criteria
4. Risk mitigation strategies
5. Implementation recommendations

Return enhanced content in the same JSON structure with improvements marked.
"""
    
    def _create_technical_requirements_prompt(self, session_data: Dict[str, Any]) -> str:
        """Create prompt for technical requirements"""
        product_type = session_data.get('product_type', 'web_app')
        industry = session_data.get('industry_type', 'general')
        
        return f"""
Generate comprehensive technical requirements for a {product_type} in the {industry} industry.

PROJECT CONTEXT:
{json.dumps(session_data, indent=2)}

Please provide specific technical requirements for:
1. Performance requirements (response times, throughput, scalability)
2. Security requirements (authentication, encryption, compliance)
3. Infrastructure requirements (hosting, databases, monitoring)
4. Integration requirements (APIs, third-party services)
5. Reliability requirements (uptime, backup, disaster recovery)
6. Platform-specific requirements based on the product type

Format as a structured list with measurable criteria for each requirement.
"""
    
    def _query_claude_code(self, prompt: str) -> AIResponse:
        """Query Claude Code with the given prompt"""
        try:
            # For Claude Code, we'll create a temporary file with the prompt
            # and execute Claude Code to analyze it
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                temp_file = f.name
            
            try:
                result = self.env_manager.execute_claude_code(
                    self.current_environment,
                    f"analyze {temp_file}",
                    working_dir=os.getcwd()
                )
                
                if result.returncode == 0:
                    return AIResponse(
                        content=result.stdout,
                        success=True,
                        provider="claude-code",
                        metadata={"stderr": result.stderr}
                    )
                else:
                    return AIResponse(
                        content=f"Claude Code error: {result.stderr}",
                        success=False,
                        provider="claude-code",
                        metadata={"return_code": result.returncode}
                    )
            
            finally:
                # Clean up temp file
                os.unlink(temp_file)
                
        except Exception as e:
            return AIResponse(
                content=f"Error executing Claude Code: {str(e)}",
                success=False,
                provider="claude-code",
                metadata={"error": str(e)}
            )
    
    def _query_ollama(self, prompt: str) -> AIResponse:
        """Query Ollama with the given prompt"""
        try:
            result = self.env_manager.execute_ollama(
                self.current_environment,
                prompt
            )
            
            if "error" in result:
                return AIResponse(
                    content=f"Ollama error: {result['error']}",
                    success=False,
                    provider="ollama",
                    metadata=result
                )
            
            return AIResponse(
                content=result.get("response", "No response from Ollama"),
                success=True,
                provider="ollama",
                metadata={
                    "model": result.get("model"),
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration")
                }
            )
            
        except Exception as e:
            return AIResponse(
                content=f"Error executing Ollama: {str(e)}",
                success=False,
                provider="ollama",
                metadata={"error": str(e)}
            )
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get current AI provider status"""
        environments = self.env_manager.list_environments()
        capabilities = self.env_manager.detect_capabilities()
        
        return {
            "current_provider": self.current_provider.value,
            "current_environment": self.current_environment,
            "available_environments": list(environments.keys()),
            "system_capabilities": capabilities,
            "environments": {
                name: {
                    "provider": config.ai_provider,
                    "path": config.environment_path
                }
                for name, config in environments.items()
            }
        }
    
    def switch_provider(self, provider: AIProvider, environment_name: str = None) -> bool:
        """Switch to a different AI provider"""
        if environment_name is None:
            environment_name = provider.value
        
        env_config = self.env_manager.get_environment(environment_name)
        if env_config and env_config.ai_provider == provider.value:
            self.current_provider = provider
            self.current_environment = environment_name
            return True
        
        return False