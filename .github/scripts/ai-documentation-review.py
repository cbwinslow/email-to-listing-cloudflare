#!/usr/bin/env python3
"""
AI-Powered Documentation Review and Generation
Analyzes codebases and generates comprehensive documentation
"""

import os
import sys
import json
import requests
from pathlib import Path
import subprocess
from typing import List, Dict, Any
import re

class AIDocumentationReviewer:
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

    def analyze_codebase_structure(self) -> Dict[str, Any]:
        """Analyze the overall codebase structure"""
        structure = {
            'languages': {},
            'frameworks': [],
            'entry_points': [],
            'config_files': [],
            'documentation_files': []
        }

        # Analyze package.json for Node.js projects
        if Path('package.json').exists():
            with open('package.json', 'r') as f:
                package = json.load(f)
                structure['frameworks'].append('Node.js')
                if 'dependencies' in package:
                    deps = package['dependencies']
                    if 'react' in deps:
                        structure['frameworks'].append('React')
                    if 'next' in deps:
                        structure['frameworks'].append('Next.js')
                    if '@cloudflare/workers-types' in deps:
                        structure['frameworks'].append('Cloudflare Workers')

        # Find entry points
        entry_patterns = [
            'src/index.js', 'src/index.ts', 'src/main.js', 'src/main.ts',
            'src/app.js', 'src/app.ts', 'index.js', 'index.ts',
            'src/App.tsx', 'src/App.jsx'
        ]

        for pattern in entry_patterns:
            if Path(pattern).exists():
                structure['entry_points'].append(pattern)

        # Find config files
        config_files = [
            'package.json', 'tsconfig.json', 'webpack.config.js',
            'vite.config.js', 'next.config.js', 'wrangler.toml',
            '.eslintrc.json', 'jest.config.js', 'vitest.config.js'
        ]

        for config in config_files:
            if Path(config).exists():
                structure['config_files'].append(config)

        # Find documentation
        docs = ['README.md', 'CHANGELOG.md', 'API.md', 'docs/']
        for doc in docs:
            if Path(doc).exists():
                structure['documentation_files'].append(doc)

        return structure

    def generate_readme(self, structure: Dict[str, Any]) -> str:
        """Generate comprehensive README using AI"""
        client_config = self.get_ai_client()

        prompt = f"""
        Generate a comprehensive README.md for this project based on the following structure analysis:

        Project Structure:
        {json.dumps(structure, indent=2)}

        Please create a professional README.md that includes:
        1. Project title and description
        2. Features list
        3. Installation instructions
        4. Usage examples
        5. API documentation (if applicable)
        6. Contributing guidelines
        7. License information

        Make it well-formatted with proper markdown syntax, badges, and clear sections.
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
                    'temperature': 0.7,
                    'max_tokens': 3000
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return self.generate_basic_readme(structure)

        except Exception as e:
            print(f"AI README generation failed: {e}")
            return self.generate_basic_readme(structure)

    def generate_basic_readme(self, structure: Dict[str, Any]) -> str:
        """Generate basic README when AI fails"""
        frameworks = ', '.join(structure.get('frameworks', []))
        entry_points = ', '.join(structure.get('entry_points', []))

        readme = f"""# Project

A {frameworks} application.

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Running the Application

```bash
npm run dev
```

### Building

```bash
npm run build
```

## 📁 Project Structure

- **Entry Points:** {entry_points}
- **Frameworks:** {frameworks}
- **Configuration:** {', '.join(structure.get('config_files', []))}

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.
"""
        return readme

    def analyze_documentation_gaps(self) -> Dict[str, Any]:
        """Analyze what documentation is missing"""
        gaps = {
            'missing_files': [],
            'incomplete_sections': [],
            'code_without_docs': []
        }

        # Check for common documentation files
        required_docs = ['README.md', 'CHANGELOG.md', 'CONTRIBUTING.md']
        for doc in required_docs:
            if not Path(doc).exists():
                gaps['missing_files'].append(doc)

        # Check README completeness
        if Path('README.md').exists():
            with open('README.md', 'r') as f:
                content = f.read().lower()

            required_sections = ['installation', 'usage', 'contributing', 'license']
            for section in required_sections:
                if f'## {section}' not in content and f'# {section}' not in content:
                    gaps['incomplete_sections'].append(section)

        return gaps

    def generate_api_documentation(self) -> str:
        """Generate API documentation from code analysis"""
        # This would analyze exported functions, classes, etc.
        # For now, return a basic template
        return """# API Documentation

## Classes

## Functions

## Types

## Examples
"""

    def run_documentation_review(self):
        """Main documentation review execution"""
        print("📚 Starting AI Documentation Review...")

        structure = self.analyze_codebase_structure()
        gaps = self.analyze_documentation_gaps()

        print("🔍 Analyzing documentation gaps...")
        print(f"📄 Structure: {structure}")
        print(f"🚫 Gaps: {gaps}")

        # Generate README if missing or incomplete
        if not Path('README.md').exists() or gaps['incomplete_sections']:
            print("📝 Generating README.md...")
            readme_content = self.generate_readme(structure)
            with open('README.md', 'w') as f:
                f.write(readme_content)

        # Generate API docs
        if not Path('API.md').exists():
            print("📖 Generating API.md...")
            api_content = self.generate_api_documentation()
            with open('API.md', 'w') as f:
                f.write(api_content)

        # Create documentation review report
        report = f"""# 📚 AI Documentation Review Report

## 📊 Project Analysis

**Frameworks Detected:** {', '.join(structure.get('frameworks', []))}
**Entry Points:** {', '.join(structure.get('entry_points', []))}
**Configuration Files:** {', '.join(structure.get('config_files', []))}

## 🚫 Documentation Gaps Found

### Missing Files
{chr(10).join(f"- {file}" for file in gaps.get('missing_files', [])) or "None"}

### Incomplete Sections
{chr(10).join(f"- {section}" for section in gaps.get('incomplete_sections', [])) or "None"}

## ✅ Actions Taken

- {'✅ Generated README.md' if not Path('README.md').exists() else '✅ Updated README.md'}
- {'✅ Generated API.md' if not Path('API.md').exists() else '✅ API.md already exists'}

## 📋 Recommendations

1. Review generated documentation for accuracy
2. Add code examples and usage instructions
3. Include architecture diagrams if applicable
4. Add troubleshooting section
5. Document deployment process

---
*Generated by AI Documentation Reviewer*
"""

        with open('ai-documentation-review.md', 'w') as f:
            f.write(report)

        print("✅ AI Documentation Review completed!")
        print("📋 Report saved to ai-documentation-review.md")

if __name__ == "__main__":
    reviewer = AIDocumentationReviewer()
    reviewer.run_documentation_review()