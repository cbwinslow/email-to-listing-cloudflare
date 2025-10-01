#!/usr/bin/env python3
"""
AI-Powered Code Review using LocalAI/OpenRouter
Performs comprehensive code analysis, bug detection, and improvement suggestions
"""

import os
import sys
import json
import requests
from pathlib import Path
import subprocess
from typing import List, Dict, Any
import re

class AICodeReviewer:
    def __init__(self):
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.localai_url = os.getenv('LOCALAI_BASE_URL', 'http://localhost:8080')
        self.use_localai = bool(self.localai_url and not self.openrouter_key)

        # Supported file extensions
        self.code_extensions = {
            '.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.cpp', '.c', '.cs',
            '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.clj'
        }

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

    def get_changed_files(self) -> List[str]:
        """Get list of changed files in PR or commit"""
        try:
            if os.getenv('GITHUB_EVENT_NAME') == 'pull_request':
                # Get changed files from PR
                result = subprocess.run(
                    ['gh', 'pr', 'diff', '--name-only'],
                    capture_output=True, text=True, check=True
                )
                return result.stdout.strip().split('\n')
            else:
                # Get changed files from last commit
                result = subprocess.run(
                    ['git', 'diff', '--name-only', 'HEAD~1'],
                    capture_output=True, text=True, check=True
                )
                return result.stdout.strip().split('\n')
        except subprocess.CalledProcessError:
            return []

    def read_file_content(self, file_path: str) -> str:
        """Read file content safely"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def analyze_code_with_ai(self, code: str, file_path: str) -> Dict[str, Any]:
        """Analyze code using AI"""
        client_config = self.get_ai_client()

        prompt = f"""
        Analyze this code file and provide a comprehensive review:

        File: {file_path}
        Code:
        ```{self.get_language_from_extension(file_path)}
        {code}
        ```

        Please provide:
        1. Code quality assessment (1-10 scale)
        2. Potential bugs or issues
        3. Security vulnerabilities
        4. Performance concerns
        5. Best practice violations
        6. Suggested improvements
        7. Code complexity analysis

        Format your response as JSON with these keys:
        - quality_score: number
        - bugs: array of strings
        - security: array of strings
        - performance: array of strings
        - best_practices: array of strings
        - improvements: array of strings
        - complexity: string
        - summary: string
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
                    'max_tokens': 2000
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']

                # Try to parse JSON response
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Fallback to structured text parsing
                    return self.parse_text_response(content)
            else:
                return self.get_fallback_analysis(file_path)

        except Exception as e:
            print(f"AI analysis failed: {e}")
            return self.get_fallback_analysis(file_path)

    def parse_text_response(self, content: str) -> Dict[str, Any]:
        """Parse text response into structured format"""
        return {
            'quality_score': 7,
            'bugs': [],
            'security': [],
            'performance': [],
            'best_practices': [],
            'improvements': [content[:500] + "..." if len(content) > 500 else content],
            'complexity': 'Medium',
            'summary': 'AI analysis completed with text response'
        }

    def get_fallback_analysis(self, file_path: str) -> Dict[str, Any]:
        """Provide basic analysis when AI fails"""
        return {
            'quality_score': 6,
            'bugs': ['Manual review recommended'],
            'security': ['Manual security review recommended'],
            'performance': ['Manual performance review recommended'],
            'best_practices': ['Follow language-specific best practices'],
            'improvements': ['Consider adding error handling', 'Add input validation'],
            'complexity': 'Unknown',
            'summary': f'Basic analysis for {file_path} - AI analysis unavailable'
        }

    def get_language_from_extension(self, file_path: str) -> str:
        """Get programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        languages = {
            '.js': 'javascript', '.ts': 'typescript', '.jsx': 'jsx',
            '.tsx': 'tsx', '.py': 'python', '.java': 'java',
            '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp',
            '.php': 'php', '.rb': 'ruby', '.go': 'go'
        }
        return languages.get(ext, 'text')

    def generate_report(self, analyses: Dict[str, Dict]) -> str:
        """Generate comprehensive review report"""
        report = "# 🤖 AI Code Review Report\n\n"

        total_score = 0
        file_count = 0

        for file_path, analysis in analyses.items():
            if not analysis:
                continue

            file_count += 1
            total_score += analysis.get('quality_score', 5)

            report += f"## 📄 {file_path}\n\n"
            report += f"**Quality Score:** {analysis.get('quality_score', 'N/A')}/10\n\n"

            sections = [
                ('🐛 Bugs', analysis.get('bugs', [])),
                ('🔒 Security Issues', analysis.get('security', [])),
                ('⚡ Performance', analysis.get('performance', [])),
                ('📋 Best Practices', analysis.get('best_practices', [])),
                ('💡 Improvements', analysis.get('improvements', []))
            ]

            for title, items in sections:
                if items:
                    report += f"### {title}\n"
                    for item in items:
                        report += f"- {item}\n"
                    report += "\n"

            if analysis.get('complexity'):
                report += f"**Complexity:** {analysis['complexity']}\n\n"

            if analysis.get('summary'):
                report += f"**Summary:** {analysis['summary']}\n\n"

            report += "---\n\n"

        if file_count > 0:
            avg_score = total_score / file_count
            report += f"## 📊 Overall Assessment\n\n"
            report += f"**Average Quality Score:** {avg_score:.1f}/10\n"
            report += f"**Files Analyzed:** {file_count}\n\n"

            if avg_score >= 8:
                report += "🎉 Excellent code quality!\n"
            elif avg_score >= 6:
                report += "👍 Good code quality with room for improvement.\n"
            else:
                report += "⚠️ Code quality needs attention.\n"

        return report

    def run_review(self):
        """Main review execution"""
        print("🤖 Starting AI Code Review...")

        changed_files = self.get_changed_files()
        code_files = [
            f for f in changed_files
            if Path(f).suffix.lower() in self.code_extensions and Path(f).exists()
        ]

        if not code_files:
            print("No code files to review")
            return

        print(f"📄 Analyzing {len(code_files)} code files...")

        analyses = {}
        for file_path in code_files[:5]:  # Limit to 5 files for demo
            print(f"🔍 Analyzing {file_path}...")
            code = self.read_file_content(file_path)
            if len(code) > 10000:  # Limit file size
                code = code[:10000] + "\n... (truncated)"

            analysis = self.analyze_code_with_ai(code, file_path)
            analyses[file_path] = analysis

        report = self.generate_report(analyses)

        with open('ai-review-report.md', 'w') as f:
            f.write(report)

        print("✅ AI Code Review completed!")
        print("📋 Report saved to ai-review-report.md")

if __name__ == "__main__":
    reviewer = AICodeReviewer()
    reviewer.run_review()