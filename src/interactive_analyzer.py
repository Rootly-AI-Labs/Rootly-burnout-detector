"""
Interactive burnout analysis using smolagents and LLMs.
"""

import os
import logging
from typing import Any, Dict
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

# Reduce LiteLLM logging noise
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

try:
    from smolagents import CodeAgent, HfApiModel, LiteLLMModel, PythonInterpreterTool
    SMOLAGENTS_AVAILABLE = True
except ImportError as e:
    SMOLAGENTS_AVAILABLE = False
    print(f"Import error: {e}")

from burnout_tools import BurnoutDataTool, TrendAnalysisTool, RecommendationTool


class InteractiveAnalyzer:
    """Interactive analyzer for burnout data using LLMs."""
    
    def __init__(self, analysis_results: Dict[str, Any]):
        if not SMOLAGENTS_AVAILABLE:
            raise ImportError(
                "smolagents not available. Install with: pip install smolagents>=0.1.0"
            )
        
        self.results = analysis_results
        self.console = Console()
        self.agent: Optional[CodeAgent] = None
        self.model = None
        
        # Create custom tools
        self.burnout_tool = BurnoutDataTool(analysis_results)
        self.trend_tool = TrendAnalysisTool(analysis_results)
        self.recommendation_tool = RecommendationTool(analysis_results)
    
    def setup_llm(self) -> bool:
        """Setup LLM based on available API keys."""
        self.console.print("\n[bold blue]Setting up LLM for interactive analysis...[/bold blue]")
        
        # Check for available API keys
        available_models = []
        
        if os.getenv("OPENAI_API_KEY"):
            available_models.append(("OpenAI GPT-4", "openai"))
        if os.getenv("ANTHROPIC_API_KEY"):
            available_models.append(("Anthropic Claude", "anthropic"))
        if os.getenv("HF_TOKEN"):
            available_models.append(("Hugging Face (Free)", "huggingface"))
        
        if not available_models:
            self.console.print("[red]No LLM API keys found![/red]")
            self.console.print("\nTo use interactive mode, set one of:")
            self.console.print("• OPENAI_API_KEY (for GPT-4)")
            self.console.print("• ANTHROPIC_API_KEY (for Claude)")
            self.console.print("• HF_TOKEN (for Hugging Face - free tier)")
            self.console.print("\nExample: export OPENAI_API_KEY='your-key-here'")
            return False
        
        # Let user choose model if multiple available
        if len(available_models) == 1:
            model_name, model_type = available_models[0]
            self.console.print(f"[green]Using {model_name}[/green]")
        else:
            self.console.print("\n[bold]Multiple LLMs available:[/bold]")
            table = Table()
            table.add_column("Option", style="cyan")
            table.add_column("Model", style="green")
            
            for i, (model_name, _) in enumerate(available_models, 1):
                table.add_row(str(i), model_name)
            
            self.console.print(table)
            
            while True:
                try:
                    choice = int(Prompt.ask("Choose model", default="1"))
                    if 1 <= choice <= len(available_models):
                        model_name, model_type = available_models[choice - 1]
                        break
                    else:
                        self.console.print("[red]Invalid choice. Try again.[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a number.[/red]")
        
        # Initialize the chosen model
        try:
            if model_type == "openai":
                self.model = LiteLLMModel("gpt-4")
            elif model_type == "anthropic":
                self.model = LiteLLMModel("claude-3-5-sonnet-20241022")
            elif model_type == "huggingface":
                self.model = HfApiModel("microsoft/DialoGPT-large")
            
            self.console.print(f"[green]✓ {model_name} initialized successfully[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Failed to initialize {model_name}: {str(e)}[/red]")
            return False
    
    def create_agent(self) -> bool:
        """Create the smolagents agent with custom tools."""
        if not self.model:
            return False
        
        try:
            # Create agent with custom tools
            tools = [
                self.burnout_tool,
                self.trend_tool, 
                self.recommendation_tool,
                PythonInterpreterTool()
            ]
            
            self.agent = CodeAgent(
                tools=tools,
                model=self.model,
                add_base_tools=False  # Only use our custom tools
            )
            
            self.console.print("[green]✓ Interactive agent created successfully[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Failed to create agent: {str(e)}[/red]")
            return False
    
    def start_session(self):
        """Start the interactive analysis session."""
        if not self.setup_llm():
            return
        
        if not self.create_agent():
            return
        
        # Show welcome message and analysis summary
        self._show_welcome()
        self._show_analysis_summary()
        
        # Start interactive loop
        self._interactive_loop()
    
    def _show_welcome(self):
        """Show welcome message and instructions."""
        welcome_text = """
[bold blue]🔍 Interactive Burnout Analysis[/bold blue]

Ask questions about your burnout analysis data! Examples:
• "Which users have the highest burnout risk?"
• "What patterns do you see in the high-risk users?"
• "Give me recommendations for reducing team burnout"
• "Show me correlations between incidents and burnout scores"

Type 'help' for more examples, 'quit' or 'exit' to end.
        """
        
        panel = Panel(
            welcome_text.strip(),
            title="Welcome to Interactive Mode",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def _show_analysis_summary(self):
        """Show a quick summary of the analysis."""
        individual = self.results.get("individual_analyses", [])
        if not individual:
            return
        
        high_count = sum(1 for a in individual if a.get("risk_level") == "high")
        medium_count = sum(1 for a in individual if a.get("risk_level") == "medium") 
        low_count = sum(1 for a in individual if a.get("risk_level") == "low")
        
        metadata = self.results.get("metadata", {})
        
        table = Table(title="Analysis Overview", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Users Analyzed", str(len(individual)))
        table.add_row("Analysis Period", f"{metadata.get('days_analyzed', 'N/A')} days")
        table.add_row("High Risk", f"{high_count} users")
        table.add_row("Medium Risk", f"{medium_count} users")
        table.add_row("Low Risk", f"{low_count} users")
        table.add_row("Total Incidents", str(metadata.get('total_incidents', 'N/A')))
        
        self.console.print(table)
    
    def _interactive_loop(self):
        """Main interactive question-answer loop."""
        self.console.print("\n[bold green]Ready for questions![/bold green]")
        
        while True:
            try:
                # Get user input
                question = Prompt.ask("\n[bold cyan]Ask me anything")
                
                if not question.strip():
                    continue
                
                # Handle special commands
                if question.lower() in ["quit", "exit", "q"]:
                    self.console.print("\n[bold blue]Thanks for using interactive analysis! 👋[/bold blue]")
                    break
                elif question.lower() == "help":
                    self._show_help()
                    continue
                elif question.lower() == "summary":
                    self._show_analysis_summary()
                    continue
                
                # Process question with agent
                self.console.print("\n[dim]Thinking...[/dim]")
                
                try:
                    response = self.agent.run(question)
                    
                    # Display response in a nice panel
                    panel = Panel(
                        str(response),
                        title="Analysis Response",
                        border_style="green",
                        padding=(1, 2)
                    )
                    self.console.print(panel)
                    
                except Exception as e:
                    self.console.print(f"[red]Error processing question: {str(e)}[/red]")
                
            except KeyboardInterrupt:
                self.console.print("\n\n[bold blue]Session interrupted. Goodbye! 👋[/bold blue]")
                break
            except EOFError:
                self.console.print("\n\n[bold blue]Session ended. Goodbye! 👋[/bold blue]")
                break
    
    def _show_help(self):
        """Show help with example questions."""
        help_text = """
[bold]Example Questions:[/bold]

[cyan]Data Exploration:[/cyan]
• "Show me all high-risk users"
• "What's the burnout score for John Smith?"
• "Give me statistics about the analysis"

[cyan]Pattern Analysis:[/cyan]
• "What patterns do you see in the data?"
• "How do incidents correlate with burnout?"
• "What are the main risk factors?"

[cyan]Recommendations:[/cyan]
• "What should we do about high-risk users?"
• "Give me team-level recommendations"
• "What immediate actions are needed?"

[cyan]Trends & Insights:[/cyan]
• "Compare risk levels across the team"
• "What drives burnout in this organization?"
• "How can we prevent future burnout?"

[cyan]Special Commands:[/cyan]
• 'help' - Show this help
• 'summary' - Re-show analysis overview
• 'quit' or 'exit' - End session
        """
        
        panel = Panel(
            help_text.strip(),
            title="Help - Interactive Analysis",
            border_style="yellow",
            padding=(1, 2)
        )
        self.console.print(panel)


def check_interactive_requirements() -> tuple[bool, str]:
    """Check if interactive mode requirements are met."""
    if not SMOLAGENTS_AVAILABLE:
        return False, "smolagents not installed. Run: pip install smolagents>=0.1.0"
    
    # Check for any available API key
    api_keys = [
        ("OPENAI_API_KEY", "OpenAI"),
        ("ANTHROPIC_API_KEY", "Anthropic"),
        ("HF_TOKEN", "Hugging Face")
    ]
    
    available = []
    for env_var, provider in api_keys:
        if os.getenv(env_var):
            available.append(provider)
    
    if not available:
        return False, (
            "No LLM API keys found. Set one of:\n"
            "  • OPENAI_API_KEY (for GPT-4)\n"
            "  • ANTHROPIC_API_KEY (for Claude)\n"  
            "  • HF_TOKEN (for Hugging Face - free tier)"
        )
    
    return True, f"Interactive mode ready with {', '.join(available)}"


if __name__ == "__main__":
    # Test the interactive analyzer
    import json
    
    # Load sample results for testing
    sample_results = {
        "metadata": {
            "days_analyzed": 30,
            "total_users_analyzed": 5,
            "total_incidents": 50
        },
        "individual_analyses": [
            {
                "user_name": "John Doe",
                "risk_level": "high",
                "burnout_score": 8.5,
                "total_incidents": 15,
                "after_hours_percentage": 0.4,
                "recommendations": ["Reduce on-call load", "Take time off"]
            },
            {
                "user_name": "Jane Smith", 
                "risk_level": "medium",
                "burnout_score": 5.2,
                "total_incidents": 8,
                "after_hours_percentage": 0.2,
                "recommendations": ["Monitor workload"]
            }
        ]
    }
    
    analyzer = InteractiveAnalyzer(sample_results)
    analyzer.start_session()