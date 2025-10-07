# nibo

**High-performance Ollama-based LLM inference system for Mac**

`nibo` is a production-ready inference system for Large Language Models (LLMs) built on top of [Ollama](https://ollama.ai/). Optimized for Mac with native MPS (Metal Performance Shaders) acceleration and easy local model management.

## Features

- 🚀 **Native Mac Support**: Optimized for M1/M2/M3 Macs with MPS acceleration
- 🦙 **Ollama-Powered**: Easy model management and fast local inference
- 🌐 **REST API**: FastAPI-based server with OpenAPI documentation
- 📊 **Streaming Support**: Real-time token streaming for better UX
- 🏠 **Local Models**: Download and run models locally without API keys
- 🔧 **Easy Setup**: Simple installation with minimal dependencies
- 📈 **Memory Efficient**: Optimized for Mac hardware limitations
- 🤖 **CrewAI Integration**: Multi-agent AI workflows and task orchestration
- 🔗 **JIRA Integration**: LangChain-powered JIRA access and automation

## Python Version Management

This project uses **Python 3.10.15** as specified in `.tool-versions`. We recommend using [asdf](https://asdf-vm.com/) for consistent Python version management:

```bash
# Install asdf (if not already installed)
brew install asdf

# Add to your shell profile (~/.zshrc or ~/.bash_profile)
echo -e "\n. $(brew --prefix asdf)/libexec/asdf.sh" >> ~/.zshrc

# Install Python plugin
asdf plugin add python

# Install the project's Python version
asdf install

# Verify version
python --version  # Should show Python 3.10.15
```

**Note**: The `.tool-versions` file ensures all developers use the same Python version, preventing compatibility issues.

## JIRA Integration with CrewAI

This project includes powerful JIRA integration using CrewAI for multi-agent AI workflows and LangChain for JIRA API access.

### Setup JIRA Integration

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure JIRA credentials in `.env`:**
   ```bash
   JIRA_URL=https://your-domain.atlassian.net
   JIRA_USERNAME=your-email@company.com
   JIRA_API_TOKEN=your-api-token
   ```

3. **Get JIRA API Token:**
   - Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Click "Create API token"
   - Copy the token to your `.env` file

### JIRA + CrewAI Examples

**Run the demo:**
```bash
python scripts/jira_crewai_demo.py
```

**Key capabilities:**
- 🔍 **Smart Ticket Analysis**: AI agents analyze sprint progress and bottlenecks
- 📊 **Automated Reporting**: Generate insights on team workload and project status
- 🎫 **Intelligent Ticket Creation**: Create tickets with AI-generated descriptions
- 🤖 **Multi-Agent Workflows**: Coordinate multiple AI agents for complex tasks

### Example: Automated Sprint Analysis

```python
from crewai import Agent, Task, Crew
from langchain_community.tools.jira.tool import JiraQueryRun

# Create JIRA specialist agent
jira_agent = Agent(
    role="JIRA Specialist",
    goal="Analyze sprint progress and identify bottlenecks",
    tools=[jira_tool],
)

# Create analysis task
task = Task(
    description="Analyze current sprint tickets and provide status report",
    agent=jira_agent,
    expected_output="Detailed sprint analysis with recommendations"
)

# Execute with CrewAI
crew = Crew(agents=[jira_agent], tasks=[task])
result = crew.kickoff()
```

### Use Cases

1. **Sprint Planning**: AI agents analyze historical data to suggest story points
2. **Burndown Prediction**: Predict sprint completion based on current velocity
3. **Blocker Detection**: Automatically identify and escalate blocked tickets
4. **Code Review Integration**: Link code reviews with JIRA tickets
5. **Release Notes**: Generate release notes from completed tickets
