#!/usr/bin/env python3
"""
CrewAI Integration for Advanced AI-Powered Development Tasks
Orchestrates multiple AI agents for comprehensive code analysis and improvement
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class AgentRole(Enum):
    CODE_REVIEWER = "code_reviewer"
    TEST_GENERATOR = "test_generator"
    DOCUMENTATION_WRITER = "documentation_writer"
    REFACTORING_EXPERT = "refactoring_expert"
    ARCHITECTURE_ANALYST = "architecture_analyst"
    SECURITY_AUDITOR = "security_auditor"

@dataclass
class CrewAgent:
    role: AgentRole
    name: str
    goal: str
    backstory: str
    tools: List[str]

@dataclass
class Task:
    description: str
    agent: CrewAgent
    expected_output: str
    context: Dict[str, Any]

class CrewAIOrchestrator:
    def __init__(self):
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.localai_url = os.getenv('LOCALAI_BASE_URL', 'http://localhost:8080')
        self.use_localai = bool(self.localai_url and not self.openrouter_key)

        # Initialize crew agents
        self.agents = self.initialize_agents()

    def get_ai_client(self):
        """Get AI client configuration"""
        if self.use_localai:
            return {
                'base_url': f"{self.localai_url}/v1",
                'api_key': 'localai'
            }
        else:
            return {
                'base_url': 'https://openrouter.ai/api/v1',
                'api_key': self.openrouter_key
            }

    def initialize_agents(self) -> Dict[AgentRole, CrewAgent]:
        """Initialize the AI agent crew"""
        return {
            AgentRole.CODE_REVIEWER: CrewAgent(
                role=AgentRole.CODE_REVIEWER,
                name="CodeReviewer",
                goal="Perform comprehensive code reviews identifying bugs, security issues, and improvements",
                backstory="Expert code reviewer with 10+ years experience in multiple programming languages and frameworks",
                tools=["code_analysis", "security_scanner", "performance_profiler"]
            ),

            AgentRole.TEST_GENERATOR: CrewAgent(
                role=AgentRole.TEST_GENERATOR,
                name="TestGenerator",
                goal="Generate comprehensive test suites covering all code paths and edge cases",
                backstory="Testing expert specializing in unit, integration, and E2E test generation",
                tools=["test_framework", "coverage_analyzer", "mock_generator"]
            ),

            AgentRole.DOCUMENTATION_WRITER: CrewAgent(
                role=AgentRole.DOCUMENTATION_WRITER,
                name="DocumentationWriter",
                goal="Create comprehensive documentation including README, API docs, and code comments",
                backstory="Technical writer with expertise in creating clear, comprehensive documentation",
                tools=["markdown_generator", "api_extractor", "diagram_creator"]
            ),

            AgentRole.REFACTORING_EXPERT: CrewAgent(
                role=AgentRole.REFACTORING_EXPERT,
                name="RefactoringExpert",
                goal="Identify refactoring opportunities and provide actionable improvement suggestions",
                backstory="Code refactoring specialist focusing on maintainability, performance, and best practices",
                tools=["complexity_analyzer", "pattern_recognizer", "optimization_suggester"]
            ),

            AgentRole.ARCHITECTURE_ANALYST: CrewAgent(
                role=AgentRole.ARCHITECTURE_ANALYST,
                name="ArchitectureAnalyst",
                goal="Analyze codebase architecture and provide structural improvement recommendations",
                backstory="Software architect with expertise in system design and architectural patterns",
                tools=["architecture_scanner", "dependency_analyzer", "scalability_assessor"]
            ),

            AgentRole.SECURITY_AUDITOR: CrewAgent(
                role=AgentRole.SECURITY_AUDITOR,
                name="SecurityAuditor",
                goal="Identify security vulnerabilities and provide remediation recommendations",
                backstory="Security expert specializing in application security and vulnerability assessment",
                tools=["vulnerability_scanner", "owasp_checker", "encryption_validator"]
            )
        }

    def create_tasks(self, codebase_analysis: Dict[str, Any]) -> List[Task]:
        """Create tasks for the AI crew based on codebase analysis"""
        tasks = []

        # Code review task
        tasks.append(Task(
            description="Perform comprehensive code review of the entire codebase",
            agent=self.agents[AgentRole.CODE_REVIEWER],
            expected_output="Detailed code review report with bugs, security issues, and improvement suggestions",
            context={"codebase": codebase_analysis, "focus_areas": ["bugs", "security", "performance"]}
        ))

        # Test generation task
        tasks.append(Task(
            description="Generate comprehensive test suites for all code components",
            agent=self.agents[AgentRole.TEST_GENERATOR],
            expected_output="Complete test files covering unit, integration, and E2E scenarios",
            context={"codebase": codebase_analysis, "test_types": ["unit", "integration", "e2e"]}
        ))

        # Documentation task
        tasks.append(Task(
            description="Create comprehensive documentation for the project",
            agent=self.agents[AgentRole.DOCUMENTATION_WRITER],
            expected_output="README, API docs, and inline code documentation",
            context={"codebase": codebase_analysis, "doc_types": ["readme", "api", "inline"]}
        ))

        # Refactoring task
        tasks.append(Task(
            description="Analyze code for refactoring opportunities and improvements",
            agent=self.agents[AgentRole.REFACTORING_EXPERT],
            expected_output="Refactoring recommendations with effort estimates and impact analysis",
            context={"codebase": codebase_analysis, "focus_areas": ["maintainability", "performance", "readability"]}
        ))

        # Architecture analysis task
        tasks.append(Task(
            description="Analyze system architecture and provide structural recommendations",
            agent=self.agents[AgentRole.ARCHITECTURE_ANALYST],
            expected_output="Architecture assessment and improvement recommendations",
            context={"codebase": codebase_analysis, "analysis_type": "architecture"}
        ))

        # Security audit task
        tasks.append(Task(
            description="Perform security audit and vulnerability assessment",
            agent=self.agents[AgentRole.SECURITY_AUDITOR],
            expected_output="Security report with vulnerabilities and remediation steps",
            context={"codebase": codebase_analysis, "audit_type": "comprehensive"}
        ))

        return tasks

    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task using AI"""
        client_config = self.get_ai_client()

        prompt = f"""
        You are {task.agent.name}, a {task.agent.role.value.replace('_', ' ')}.

        Your Background: {task.agent.backstory}
        Your Goal: {task.agent.goal}

        Task: {task.description}
        Expected Output: {task.expected_output}

        Context: {json.dumps(task.context, indent=2)}

        Available Tools: {', '.join(task.agent.tools)}

        Please provide a comprehensive response addressing the task requirements.
        Be specific, actionable, and professional in your analysis and recommendations.
        """

        try:
            response = requests.post(
                f"{client_config['base_url']}/chat/completions",
                headers={
                    'Authorization': f"Bearer {client_config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'anthropic/claude-3-haiku' if not self.use_localai else 'local-model',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.3,
                    'max_tokens': 3000
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']

                return {
                    'agent': task.agent.name,
                    'role': task.agent.role.value,
                    'task': task.description,
                    'output': content,
                    'success': True
                }
            else:
                return {
                    'agent': task.agent.name,
                    'role': task.agent.role.value,
                    'task': task.description,
                    'output': f"API Error: {response.status_code}",
                    'success': False
                }

        except Exception as e:
            return {
                'agent': task.agent.name,
                'role': task.agent.role.value,
                'task': task.description,
                'output': f"Error: {e}",
                'success': False
            }

    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze the current codebase structure"""
        analysis = {
            'languages': set(),
            'frameworks': [],
            'files': [],
            'entry_points': [],
            'config_files': [],
            'test_coverage': 0
        }

        # Analyze package.json
        if Path('package.json').exists():
            with open('package.json', 'r') as f:
                package = json.load(f)
                analysis['frameworks'].append('Node.js')

                deps = package.get('dependencies', {})
                if 'react' in deps:
                    analysis['frameworks'].append('React')
                if 'next' in deps:
                    analysis['frameworks'].append('Next.js')
                if '@cloudflare/workers-types' in deps:
                    analysis['frameworks'].append('Cloudflare Workers')

        # Find code files
        code_extensions = ['*.js', '*.ts', '*.jsx', '*.tsx', '*.py']
        for ext in code_extensions:
            analysis['files'].extend([str(f) for f in Path('.').glob(f'**/{ext}')])

        # Determine languages
        for file in analysis['files']:
            if file.endswith(('.js', '.jsx')):
                analysis['languages'].add('JavaScript')
            elif file.endswith(('.ts', '.tsx')):
                analysis['languages'].add('TypeScript')
            elif file.endswith('.py'):
                analysis['languages'].add('Python')

        analysis['languages'] = list(analysis['languages'])
        return analysis

    def generate_crew_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive crew execution report"""
        report = "# 🤖 CrewAI Execution Report\n\n"
        report += f"## 📊 Overview\n\n"
        report += f"- **Agents Deployed:** {len(self.agents)}\n"
        report += f"- **Tasks Executed:** {len(results)}\n"
        report += f"- **Successful Tasks:** {sum(1 for r in results if r['success'])}\n"
        report += f"- **Failed Tasks:** {sum(1 for r in results if not r['success'])}\n\n"

        # Agent performance
        report += "## 👥 Agent Performance\n\n"
        for result in results:
            status = "✅" if result['success'] else "❌"
            report += f"### {status} {result['agent']} ({result['role'].replace('_', ' ')})\n\n"
            report += f"**Task:** {result['task']}\n\n"

            if result['success']:
                # Truncate long outputs for readability
                output = result['output']
                if len(output) > 1000:
                    output = output[:1000] + "\n\n[...truncated for brevity...]"
                report += f"**Output:**\n{output}\n\n"
            else:
                report += f"**Error:** {result['output']}\n\n"

            report += "---\n\n"

        # Recommendations summary
        report += "## 💡 Key Recommendations\n\n"

        successful_results = [r for r in results if r['success']]
        for result in successful_results:
            if "recommendations" in result['output'].lower() or "suggestions" in result['output'].lower():
                report += f"### From {result['agent']}\n"
                # Extract key recommendations (simplified)
                lines = result['output'].split('\n')
                recommendations = [line for line in lines if any(keyword in line.lower() for keyword in
                    ['recommend', 'suggest', 'should', 'consider', 'improve', 'fix'])]
                for rec in recommendations[:3]:  # Limit to top 3
                    report += f"- {rec.strip()}\n"
                report += "\n"

        report += "## 🎯 Next Steps\n\n"
        report += "1. **Review Outputs**: Examine each agent's recommendations\n"
        report += "2. **Prioritize Actions**: Focus on high-impact, low-effort improvements\n"
        report += "3. **Implement Changes**: Apply suggestions incrementally\n"
        report += "4. **Re-run Analysis**: Verify improvements with follow-up analysis\n"
        report += "5. **Iterate**: Use CrewAI regularly for continuous improvement\n\n"

        report += "---\n*Generated by CrewAI Orchestrator*"

        return report

    def run_crew_execution(self):
        """Main CrewAI execution"""
        print("🚀 Starting CrewAI Orchestration...")

        # Analyze codebase
        print("🔍 Analyzing codebase...")
        codebase_analysis = self.analyze_codebase()
        print(f"📊 Found {len(codebase_analysis['files'])} files, {len(codebase_analysis['languages'])} languages")

        # Create tasks
        print("📋 Creating task assignments...")
        tasks = self.create_tasks(codebase_analysis)
        print(f"🎯 Created {len(tasks)} tasks for {len(self.agents)} agents")

        # Execute tasks
        results = []
        for i, task in enumerate(tasks, 1):
            print(f"🤖 Executing Task {i}/{len(tasks)}: {task.agent.name} - {task.description[:50]}...")
            result = self.execute_task(task)
            results.append(result)

            if result['success']:
                print(f"✅ {task.agent.name} completed successfully")
            else:
                print(f"❌ {task.agent.name} failed: {result['output']}")

        # Generate comprehensive report
        print("📝 Generating comprehensive report...")
        report = self.generate_crew_report(results)

        with open('crewai-execution-report.md', 'w') as f:
            f.write(report)

        # Save individual agent outputs
        crew_output_dir = Path('crewai-outputs')
        crew_output_dir.mkdir(exist_ok=True)

        for result in results:
            output_file = crew_output_dir / f"{result['role']}-output.md"
            with open(output_file, 'w') as f:
                f.write(f"# {result['agent']} Report\n\n")
                f.write(f"**Task:** {result['task']}\n\n")
                f.write(f"**Status:** {'✅ Success' if result['success'] else '❌ Failed'}\n\n")
                f.write(f"## Output\n\n{result['output']}")

        print("✅ CrewAI Execution completed!")
        print(f"📋 Main report: crewai-execution-report.md")
        print(f"📁 Individual outputs: crewai-outputs/")
        print(f"👥 Agents deployed: {len(self.agents)}")
        print(f"🎯 Tasks completed: {sum(1 for r in results if r['success'])}/{len(results)}")

if __name__ == "__main__":
    crew = CrewAIOrchestrator()
    crew.run_crew_execution()