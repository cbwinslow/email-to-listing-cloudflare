#!/usr/bin/env python3
"""
AI-Powered Code Refactoring and Improvement Suggestions
Analyzes codebases and provides refactoring recommendations
"""

import os
import sys
import json
import requests
from pathlib import Path
import subprocess
from typing import List, Dict, Any
import re

class AIRefactor:
    def __init__(self):
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.localai_url = os.getenv('LOCALAI_BASE_URL', 'http://localhost:8080')
        self.use_localai = bool(self.localai_url and not self.openrouter_key)

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

    def analyze_code_complexity(self, code: str, file_path: str) -> Dict[str, Any]:
        """Analyze code complexity and maintainability"""
        lines = len(code.split('\n'))
        functions = len(re.findall(r'(?:function|=>|\w+\s*\()', code))
        classes = len(re.findall(r'class\s+\w+', code))
        imports = len(re.findall(r'^import|^from', code, re.MULTILINE))

        # Simple complexity metrics
        complexity = {
            'lines': lines,
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'complexity_score': min(10, (lines // 50) + (functions // 5) + (classes // 2))
        }

        return complexity

    def get_refactoring_suggestions(self, code: str, file_path: str, complexity: Dict) -> Dict[str, Any]:
        """Get AI-powered refactoring suggestions"""
        client_config = self.get_ai_client()

        language = self.get_language_from_path(file_path)

        prompt = f"""
        Analyze this {language} code and provide refactoring suggestions:

        File: {file_path}
        Complexity: {json.dumps(complexity, indent=2)}

        Code:
        ```{language}
        {code[:2000]}{"..." if len(code) > 2000 else ""}
        ```

        Please provide:
        1. Code quality assessment
        2. Refactoring opportunities
        3. Performance improvements
        4. Best practice recommendations
        5. Specific code changes suggested
        6. Estimated effort for each suggestion

        Format as JSON with these keys:
        - quality_score: number (1-10)
        - refactoring_opportunities: array of objects with {title, description, effort, impact}
        - performance_improvements: array of strings
        - best_practices: array of strings
        - code_suggestions: array of strings
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
                    'temperature': 0.4,
                    'max_tokens': 2500
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']

                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return self.parse_refactor_response(content)
            else:
                return self.get_basic_refactoring_suggestions(file_path, complexity)

        except Exception as e:
            print(f"AI refactoring analysis failed: {e}")
            return self.get_basic_refactoring_suggestions(file_path, complexity)

    def parse_refactor_response(self, content: str) -> Dict[str, Any]:
        """Parse text response into structured format"""
        return {
            'quality_score': 7,
            'refactoring_opportunities': [
                {
                    'title': 'Code Review',
                    'description': 'Manual review recommended',
                    'effort': 'Medium',
                    'impact': 'High'
                }
            ],
            'performance_improvements': ['Consider performance optimizations'],
            'best_practices': ['Follow language best practices'],
            'code_suggestions': [content[:300] + "..." if len(content) > 300 else content],
            'summary': 'AI analysis completed with suggestions'
        }

    def get_basic_refactoring_suggestions(self, file_path: str, complexity: Dict) -> Dict[str, Any]:
        """Provide basic refactoring suggestions"""
        suggestions = []

        if complexity['lines'] > 300:
            suggestions.append({
                'title': 'File Size Reduction',
                'description': 'Consider splitting large files into smaller modules',
                'effort': 'High',
                'impact': 'Medium'
            })

        if complexity['functions'] > 10:
            suggestions.append({
                'title': 'Function Extraction',
                'description': 'Extract complex functions into smaller, focused functions',
                'effort': 'Medium',
                'impact': 'High'
            })

        if complexity['complexity_score'] > 7:
            suggestions.append({
                'title': 'Complexity Reduction',
                'description': 'Refactor to reduce cyclomatic complexity',
                'effort': 'High',
                'impact': 'High'
            })

        return {
            'quality_score': max(1, 10 - complexity['complexity_score']),
            'refactoring_opportunities': suggestions,
            'performance_improvements': [
                'Consider memoization for expensive operations',
                'Review algorithm complexity',
                'Optimize data structures'
            ],
            'best_practices': [
                'Add error handling',
                'Include input validation',
                'Add comprehensive documentation'
            ],
            'code_suggestions': [
                'Extract magic numbers to constants',
                'Use early returns to reduce nesting',
                'Add type hints (if applicable)'
            ],
            'summary': f'Basic refactoring analysis for {file_path}'
        }

    def get_language_from_path(self, file_path: str) -> str:
        """Get programming language from file path"""
        ext = Path(file_path).suffix.lower()
        languages = {
            '.js': 'javascript', '.ts': 'typescript',
            '.jsx': 'jsx', '.tsx': 'tsx', '.py': 'python',
            '.java': 'java', '.cpp': 'cpp', '.c': 'c'
        }
        return languages.get(ext, 'text')

    def generate_refactor_report(self, analyses: Dict[str, Dict]) -> str:
        """Generate comprehensive refactoring report"""
        report = "# 🔄 AI Code Refactoring Report\n\n"

        total_score = 0
        file_count = 0
        all_suggestions = []

        for file_path, analysis in analyses.items():
            if not analysis:
                continue

            file_count += 1
            total_score += analysis.get('quality_score', 5)

            report += f"## 📄 {file_path}\n\n"
            report += f"**Quality Score:** {analysis.get('quality_score', 'N/A')}/10\n\n"

            # Refactoring opportunities
            opportunities = analysis.get('refactoring_opportunities', [])
            if opportunities:
                report += "### 🔧 Refactoring Opportunities\n"
                for opp in opportunities:
                    report += f"**{opp.get('title', 'Suggestion')}**\n"
                    report += f"- **Description:** {opp.get('description', 'N/A')}\n"
                    report += f"- **Effort:** {opp.get('effort', 'Unknown')}\n"
                    report += f"- **Impact:** {opp.get('impact', 'Unknown')}\n\n"
                    all_suggestions.append(opp)

            # Performance improvements
            perf = analysis.get('performance_improvements', [])
            if perf:
                report += "### ⚡ Performance Improvements\n"
                for item in perf:
                    report += f"- {item}\n"
                report += "\n"

            # Best practices
            practices = analysis.get('best_practices', [])
            if practices:
                report += "### 📋 Best Practices\n"
                for practice in practices:
                    report += f"- {practice}\n"
                report += "\n"

            # Code suggestions
            suggestions = analysis.get('code_suggestions', [])
            if suggestions:
                report += "### 💡 Code Suggestions\n"
                for suggestion in suggestions:
                    report += f"- {suggestion}\n"
                report += "\n"

            if analysis.get('summary'):
                report += f"**Summary:** {analysis['summary']}\n\n"

            report += "---\n\n"

        # Overall assessment
        if file_count > 0:
            avg_score = total_score / file_count
            report += f"## 📊 Overall Assessment\n\n"
            report += f"**Average Quality Score:** {avg_score:.1f}/10\n"
            report += f"**Files Analyzed:** {file_count}\n"
            report += f"**Total Suggestions:** {len(all_suggestions)}\n\n"

            # Prioritize suggestions by impact
            high_impact = [s for s in all_suggestions if s.get('impact') == 'High']
            if high_impact:
                report += "### 🎯 High Impact Suggestions\n"
                for suggestion in high_impact[:5]:
                    report += f"- **{suggestion.get('title')}**: {suggestion.get('description')} (Effort: {suggestion.get('effort')})\n"
                report += "\n"

            if avg_score >= 8:
                report += "🎉 Excellent code quality! Minor improvements suggested.\n"
            elif avg_score >= 6:
                report += "👍 Good code with opportunities for enhancement.\n"
            else:
                report += "⚠️ Significant refactoring recommended.\n"

        return report

    def run_refactoring_analysis(self):
        """Main refactoring analysis execution"""
        print("🔄 Starting AI Code Refactoring Analysis...")

        # Get changed files or analyze key files
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1'],
                capture_output=True, text=True, check=True
            )
            changed_files = result.stdout.strip().split('\n')
        except:
            # Fallback: analyze some key files
            changed_files = ['package.json', 'README.md']

        # Filter for code files
        code_extensions = ['.js', '.ts', '.jsx', '.tsx', '.py', '.java']
        code_files = [
            f for f in changed_files
            if any(f.endswith(ext) for ext in code_extensions) and Path(f).exists()
        ]

        if not code_files:
            # Analyze some default files
            default_files = ['package.json', 'README.md', 'test-generator.js']
            code_files = [f for f in default_files if Path(f).exists()]

        print(f"📄 Analyzing {len(code_files)} files for refactoring opportunities...")

        analyses = {}
        for file_path in code_files[:3]:  # Limit for demo
            print(f"🔍 Analyzing {file_path}...")

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()

                complexity = self.analyze_code_complexity(code, file_path)
                suggestions = self.get_refactoring_suggestions(code, file_path, complexity)

                analyses[file_path] = suggestions

            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                analyses[file_path] = {
                    'quality_score': 5,
                    'summary': f'Analysis failed: {e}'
                }

        report = self.generate_refactor_report(analyses)

        with open('ai-refactor-suggestions.md', 'w') as f:
            f.write(report)

        print("✅ AI Refactoring Analysis completed!")
        print("📋 Report saved to ai-refactor-suggestions.md")

if __name__ == "__main__":
    refactor = AIRefactor()
    refactor.run_refactoring_analysis()