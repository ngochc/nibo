#!/usr/bin/env python3
"""
Simple JIRA Ticket Report using Ollama
Get all unfinished tickets and generate a report
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_report_filename(project_key=None):
    """Create a timestamped filename for the report."""
    # Create base data and reports directory structure
    data_dir = "data"
    base_reports_dir = os.path.join(data_dir, "reports")
    os.makedirs(base_reports_dir, exist_ok=True)
    
    # Create project-specific subdirectory if project is specified
    if project_key:
        project_dir = os.path.join(base_reports_dir, project_key.lower())
        os.makedirs(project_dir, exist_ok=True)
        reports_dir = project_dir
    else:
        reports_dir = base_reports_dir
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create filename based on project
    if project_key:
        filename = f"jira_report_{timestamp}.txt"
    else:
        filename = f"jira_all_projects_report_{timestamp}.txt"
    
    return os.path.join(reports_dir, filename)


def load_project_cache():
    """Load cached project selection from previous runs."""
    data_dir = "data"
    cache_file = os.path.join(data_dir, "jira_project_cache.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                return cache.get("last_project"), cache.get("recent_projects", [])
        except Exception as e:
            print(f"⚠️  Could not load project cache: {e}")
    return None, []


def save_project_cache(project_key, recent_projects):
    """Save project selection to cache for future runs."""
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    cache_file = os.path.join(data_dir, "jira_project_cache.json")
    
    try:
        # Update recent projects list
        if project_key and project_key != 'ALL':
            if project_key in recent_projects:
                recent_projects.remove(project_key)
            recent_projects.insert(0, project_key)
            recent_projects = recent_projects[:5]  # Keep only last 5 projects
        
        cache = {
            "last_project": project_key,
            "recent_projects": recent_projects,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
            
    except Exception as e:
        print(f"⚠️  Could not save project cache: {e}")


def list_previous_reports(project_key=None):
    """List previous reports for reference."""
    data_dir = "data"
    reports_dir = os.path.join(data_dir, "reports")
    if not os.path.exists(reports_dir):
        return []
    
    reports = []
    
    # If project specified, look in project subdirectory first
    if project_key:
        project_dir = os.path.join(reports_dir, project_key.lower())
        if os.path.exists(project_dir):
            for filename in os.listdir(project_dir):
                if filename.startswith("jira_") and filename.endswith(".txt"):
                    filepath = os.path.join(project_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    reports.append({
                        'filename': f"{project_key.lower()}/{filename}",
                        'filepath': filepath,
                        'modified': datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        'size': os.path.getsize(filepath),
                        'project': project_key
                    })
    
    # Also check main reports directory
    for item in os.listdir(reports_dir):
        item_path = os.path.join(reports_dir, item)
        if os.path.isfile(item_path) and item.startswith("jira_") and item.endswith(".txt"):
            mtime = os.path.getmtime(item_path)
            reports.append({
                'filename': item,
                'filepath': item_path,
                'modified': datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
                'size': os.path.getsize(item_path),
                'project': 'ALL'
            })
        elif os.path.isdir(item_path) and not project_key:
            # List reports from project subdirectories
            for filename in os.listdir(item_path):
                if filename.startswith("jira_") and filename.endswith(".txt"):
                    filepath = os.path.join(item_path, filename)
                    mtime = os.path.getmtime(filepath)
                    reports.append({
                        'filename': f"{item}/{filename}",
                        'filepath': filepath,
                        'modified': datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        'size': os.path.getsize(filepath),
                        'project': item.upper()
                    })
    
    # Sort by modification time (newest first)
    reports.sort(key=lambda x: x['modified'], reverse=True)
    return reports


def setup_jira_connection():
    """Setup JIRA connection using PAT."""
    try:
        from atlassian import Jira
        
        jira_url = os.getenv("JIRA_URL")
        pat_token = os.getenv("JIRA_API_TOKEN")
        
        print(f"🔗 Connecting to JIRA: {jira_url}")
        
        jira = Jira(
            url=jira_url,
            token=pat_token,
            verify_ssl=True
        )
        
        # Test connection
        server_info = jira.get_server_info()
        print(f"✅ Connected to JIRA: {server_info.get('serverTitle', 'Unknown')}")
        return jira
        
    except Exception as e:
        print(f"❌ JIRA connection failed: {e}")
        return None


def get_unfinished_tickets(jira_client, project_key=None):
    """Get all unfinished tickets, optionally filtered by project."""
    try:
        # Build query for unfinished tickets
        base_query = "status NOT IN (Done, Closed, Resolved)"
        
        if project_key:
            query = f"project = {project_key} AND {base_query} ORDER BY priority DESC, created DESC"
            print(f"🔍 Searching for unfinished tickets in project {project_key}...")
        else:
            query = f"{base_query} ORDER BY priority DESC, created DESC"
            print("🔍 Searching for unfinished tickets across all projects...")
        
        issues = jira_client.jql(query, limit=50)
        issue_list = issues.get('issues', [])
        
        if project_key:
            print(f"📊 Found {len(issue_list)} unfinished tickets in {project_key}")
        else:
            print(f"📊 Found {len(issue_list)} unfinished tickets across all projects")
        
        ticket_data = []
        for issue in issue_list:
            fields = issue.get('fields', {})
            ticket_info = {
                'key': issue.get('key', 'N/A'),
                'summary': fields.get('summary', 'No summary'),
                'status': fields.get('status', {}).get('name', 'Unknown'),
                'priority': fields.get('priority', {}).get('name', 'None'),
                'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
                'project': fields.get('project', {}).get('key', 'Unknown'),
                'created': fields.get('created', 'Unknown')[:10] if fields.get('created') else 'Unknown'  # Just date part
            }
            ticket_data.append(ticket_info)
        
        return ticket_data
        
    except Exception as e:
        print(f"❌ Error fetching tickets: {e}")
        return []


def get_available_projects(jira_client, limit=None):
    """Get list of available projects."""
    try:
        print("🔍 Fetching available projects...")
        projects = jira_client.get_all_projects()
        
        print(f"📋 Found {len(projects)} total projects")
        
        # Return all projects if no limit specified
        project_list = []
        projects_to_process = projects if limit is None else projects[:limit]
        
        for project in projects_to_process:
            key = project.get('key', 'N/A')
            name = project.get('name', 'No name')
            project_type = project.get('projectTypeKey', 'Unknown')
            project_list.append({
                'key': key,
                'name': name,
                'type': project_type
            })
        
        return project_list
        
    except Exception as e:
        print(f"❌ Error fetching projects: {e}")
        return []


def search_projects(projects, search_term):
    """Search projects by key, name, or partial match."""
    if not search_term:
        return projects
    
    search_term = search_term.lower()
    matching_projects = []
    
    for project in projects:
        key = project['key'].lower()
        name = project['name'].lower()
        
        # Check if search term matches key or name
        if (search_term in key or 
            search_term in name or 
            key.startswith(search_term) or
            any(word.startswith(search_term) for word in name.split())):
            matching_projects.append(project)
    
    return matching_projects


def interactive_project_selection(jira_client):
    """Interactive project selection with search functionality."""
    print("\n🔍 Project Selection")
    print("=" * 30)
    
    # Get all projects
    all_projects = get_available_projects(jira_client)
    if not all_projects:
        print("❌ Could not fetch projects")
        return None
    
    while True:
        # Ask user for search term
        search_term = input("\nEnter project name or key to search (or press Enter to see all): ").strip()
        
        # Search for matching projects
        if search_term:
            matching_projects = search_projects(all_projects, search_term)
            if not matching_projects:
                print(f"❌ No projects found matching '{search_term}'")
                print("💡 Try a different search term or press Enter to see all projects")
                continue
        else:
            matching_projects = all_projects[:20]  # Show top 20 if no search
        
        # Display matching projects
        print(f"\n📋 Found {len(matching_projects)} matching projects:")
        if len(matching_projects) > 20:
            print("   (Showing first 20 results)")
            matching_projects = matching_projects[:20]
        
        for i, project in enumerate(matching_projects, 1):
            print(f"  {i:2d}. {project['key']:12} - {project['name'][:50]}")
        
        # Let user choose
        print(f"\n💡 Options:")
        print(f"   • Enter number (1-{len(matching_projects)}) to select a project")
        print(f"   • Enter 'all' to analyze all projects")
        print(f"   • Enter 'search' to search again")
        print(f"   • Press Enter to quit")
        
        choice = input("\nYour choice: ").strip().lower()
        
        if not choice:
            return None
        elif choice == 'all':
            return 'ALL'
        elif choice == 'search':
            continue
        else:
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(matching_projects):
                    selected_project = matching_projects[choice_num - 1]
                    print(f"✅ Selected: {selected_project['key']} - {selected_project['name']}")
                    return selected_project['key']
                else:
                    print(f"❌ Invalid choice. Please enter a number between 1 and {len(matching_projects)}")
            except ValueError:
                print("❌ Invalid input. Please enter a number, 'all', 'search', or press Enter to quit")
                continue


def setup_ollama_llm():
    """Setup Ollama LLM for CrewAI."""
    try:
        from langchain_ollama import ChatOllama
        
        # Configure Ollama
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:1b")
        
        print(f"🤖 Setting up Ollama: {ollama_model} at {ollama_base_url}")
        
        llm = ChatOllama(
            model=ollama_model,
            base_url=ollama_base_url,
            temperature=0.1,
        )
        
        # Test the connection
        response = llm.invoke("Hello, can you help analyze JIRA tickets?")
        print(f"✅ Ollama connected: {response.content[:50]}...")
        
        return llm
        
    except Exception as e:
        print(f"❌ Ollama setup failed: {e}")
        print("💡 Make sure Ollama is running: ollama serve")
        print("💡 And the model is available: ollama pull llama3.2:1b")
        return None


def create_jira_agent_with_ollama():
    """Create CrewAI agent with Ollama LLM."""
    try:
        from crewai import Agent
        import os
        
        # Set Ollama as the LLM for CrewAI
        os.environ["OPENAI_API_BASE"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        os.environ["OPENAI_MODEL_NAME"] = f"ollama/{os.getenv('OLLAMA_MODEL', 'gemma3:1b')}"
        os.environ["OPENAI_API_KEY"] = "ollama"  # Dummy key for Ollama
        
        agent = Agent(
            role="JIRA Ticket Analyst",
            goal="Analyze JIRA tickets and create clear, actionable reports",
            backstory="You are an experienced project manager who specializes in analyzing JIRA tickets and providing clear insights for development teams.",
            verbose=True,
            allow_delegation=False,
            llm=setup_ollama_llm()
        )
        
        return agent
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return None


def generate_ticket_report(tickets, use_ai=True):
    """Generate a report from ticket data."""
    if not tickets:
        return "No unfinished tickets found."
    
    # Basic report without AI
    report = f"""
📋 JIRA UNFINISHED TICKETS REPORT
{'='*50}

Total Unfinished Tickets: {len(tickets)}

SUMMARY BY STATUS:
"""
    
    # Count by status
    status_count = {}
    priority_count = {}
    project_count = {}
    
    for ticket in tickets:
        status = ticket['status']
        priority = ticket['priority']
        project = ticket['project']
        
        status_count[status] = status_count.get(status, 0) + 1
        priority_count[priority] = priority_count.get(priority, 0) + 1
        project_count[project] = project_count.get(project, 0) + 1
    
    # Add status breakdown
    for status, count in sorted(status_count.items()):
        report += f"  • {status}: {count} tickets\n"
    
    report += f"\nSUMMARY BY PRIORITY:\n"
    for priority, count in sorted(priority_count.items(), key=lambda x: x[1], reverse=True):
        report += f"  • {priority}: {count} tickets\n"
    
    report += f"\nSUMMARY BY PROJECT:\n"
    for project, count in sorted(project_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        report += f"  • {project}: {count} tickets\n"
    
    report += f"\nHIGHEST PRIORITY TICKETS:\n"
    high_priority_tickets = [t for t in tickets if t['priority'] in ['Highest', 'High']][:10]
    
    for ticket in high_priority_tickets:
        report += f"  • {ticket['key']}: {ticket['summary'][:60]}...\n"
        report += f"    Status: {ticket['status']} | Assignee: {ticket['assignee']} | Project: {ticket['project']}\n\n"
    
    # If AI is available, enhance the report
    if use_ai:
        try:
            from crewai import Task, Crew
            
            agent = create_jira_agent_with_ollama()
            if agent:
                print("🤖 Enhancing report with AI analysis...")
                
                # Create enhanced analysis task
                task = Task(
                    description=f"""Analyze the following JIRA ticket data and provide insights:

{report}

Raw ticket data: {tickets[:20]}  # First 20 tickets for analysis

Please provide:
1. Key insights about the ticket distribution
2. Potential bottlenecks or issues
3. Recommendations for the team
4. Priority suggestions based on the data

Keep the analysis concise and actionable.""",
                    agent=agent,
                    expected_output="A concise analysis with insights and recommendations based on the JIRA ticket data"
                )
                
                crew = Crew(
                    agents=[agent],
                    tasks=[task],
                    verbose=False  # Reduce verbose output
                )
                
                ai_analysis = crew.kickoff()
                report += f"\n🤖 AI ANALYSIS:\n{'='*50}\n{ai_analysis}\n"
                
        except Exception as e:
            print(f"⚠️  AI analysis failed: {e}")
            print("📊 Using basic report instead")
    
    return report


def main():
    """Main function to generate JIRA ticket report."""
    import sys
    
    print("🎯 JIRA Unfinished Tickets Report Generator")
    print("=" * 50)
    
    # Show previous reports
    previous_reports = list_previous_reports()
    if previous_reports:
        print(f"\n📚 Previous Reports (found {len(previous_reports)} reports):")
        for i, report in enumerate(previous_reports[:5], 1):  # Show last 5 reports
            size_kb = report['size'] / 1024
            project_info = f"[{report['project']}] " if report.get('project') else ""
            print(f"  {i}. {project_info}{report['filename']} ({size_kb:.1f}KB - {report['modified']})")
        if len(previous_reports) > 5:
            print(f"  ... and {len(previous_reports) - 5} more reports in ./data/reports/")
        print()
    
    # Check environment variables
    required_vars = ["JIRA_URL", "JIRA_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return
    
    # Setup JIRA connection
    jira_client = setup_jira_connection()
    if not jira_client:
        print("❌ Cannot proceed without JIRA connection")
        return
    
    # Check if user specified a project via command line
    project_key = None
    if len(sys.argv) > 1:
        project_key = sys.argv[1].upper()
        print(f"🎯 Targeting project: {project_key}")
    else:
        # Load cached project from previous runs
        last_project, recent_projects = load_project_cache()
        
        if last_project or recent_projects:
            print(f"\n� Recent Project Selections:")
            options = []
            
            if last_project:
                print(f"  1. {last_project} (last used)")
                options.append(last_project)
            
            for i, proj in enumerate(recent_projects[:4], 2 if last_project else 1):
                if proj != last_project:  # Don't duplicate last project
                    print(f"  {i}. {proj}")
                    options.append(proj)
            
            if options:
                choice = input(f"\nUse cached project? Enter number (1-{len(options)}) or press Enter to search: ").strip()
                
                if choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(options):
                        project_key = options[choice_num - 1]
                        print(f"🎯 Using cached project: {project_key}")
        
        # If no project selected from cache, do interactive selection
        if project_key is None:
            project_selection = interactive_project_selection(jira_client)
            if project_selection is None:
                print("👋 Goodbye!")
                return
            elif project_selection == 'ALL':
                project_key = None
                print("🎯 Analyzing all projects")
            else:
                project_key = project_selection
                print(f"🎯 Selected project: {project_key}")
        
        # Save the selection to cache
        save_project_cache(project_key, recent_projects)
    
    # Get unfinished tickets
    tickets = get_unfinished_tickets(jira_client, project_key)
    if not tickets:
        if project_key:
            print(f"✅ No unfinished tickets found in project {project_key}!")
        else:
            print("✅ No unfinished tickets found!")
        return
    
    # Generate report
    print("📝 Generating report...")
    
    # Check if Ollama is available for AI enhancement
    use_ai = setup_ollama_llm() is not None
    
    report = generate_ticket_report(tickets, use_ai=use_ai)
    
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # Save to file with timestamp in reports directory
    filename = create_report_filename(project_key)
        
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {filename}")
    print("✅ Report generation completed!")


if __name__ == "__main__":
    main()