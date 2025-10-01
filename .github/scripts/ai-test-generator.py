#!/usr/bin/env python3
"""
AI-Powered Test Generation
Automatically generates comprehensive tests for codebases
"""

import os
import sys
import json
import requests
from pathlib import Path
import ast
import re
from typing import List, Dict, Any

class AITestGenerator:
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

    def analyze_javascript_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript file for testable elements"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            analysis = {
                'functions': [],
                'classes': [],
                'components': [],
                'exports': [],
                'imports': []
            }

            # Extract function declarations
            func_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\('
            analysis['functions'] = re.findall(func_pattern, content)

            # Extract arrow functions assigned to variables
            arrow_pattern = r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\('
            arrow_funcs = re.findall(arrow_pattern, content)
            analysis['functions'].extend(arrow_funcs)

            # Extract class declarations
            class_pattern = r'(?:export\s+)?class\s+(\w+)'
            analysis['classes'] = re.findall(class_pattern, content)

            # Extract React components (simple heuristic)
            if 'React' in content or 'jsx' in file_path:
                component_pattern = r'(?:export\s+)?(?:const|function)\s+(\w+)\s*(?:\(|=)'
                components = re.findall(component_pattern, content)
                analysis['components'] = [c for c in components if c[0].isupper()]

            # Extract exports
            export_pattern = r'export\s+(?:const|function|class|default)?\s*(\w+)'
            analysis['exports'] = re.findall(export_pattern, content)

            return analysis

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {}

    def generate_tests_with_ai(self, analysis: Dict[str, Any], file_path: str) -> str:
        """Generate tests using AI"""
        client_config = self.get_ai_client()

        language = 'typescript' if file_path.endswith(('.ts', '.tsx')) else 'javascript'
        is_react = 'React' in str(analysis) or file_path.endswith(('.jsx', '.tsx'))

        prompt = f"""
        Generate comprehensive unit tests for this {language} file:

        File: {file_path}
        Analysis: {json.dumps(analysis, indent=2)}

        Requirements:
        1. Use modern testing framework (Vitest for JS/TS, pytest for Python)
        2. Include tests for all functions, classes, and components
        3. Test edge cases and error conditions
        4. Mock external dependencies
        5. Follow testing best practices
        6. Include proper setup and teardown
        {f'7. Use React Testing Library for React components' if is_react else ''}

        Generate complete, runnable test code with proper imports and structure.
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
                return result['choices'][0]['message']['content']
            else:
                return self.generate_basic_tests(analysis, file_path)

        except Exception as e:
            print(f"AI test generation failed: {e}")
            return self.generate_basic_tests(analysis, file_path)

    def generate_basic_tests(self, analysis: Dict[str, Any], file_path: str) -> str:
        """Generate basic test structure when AI fails"""
        test_file = Path(file_path).stem + '.test' + Path(file_path).suffix

        is_react = file_path.endswith(('.jsx', '.tsx'))
        is_typescript = file_path.endswith(('.ts', '.tsx'))

        test_content = f'''{"/** @vitest-environment jsdom */" if is_react else ""}
import {{ describe, it, expect{" , vi" if not is_react else ""} }} from 'vitest';
{"import { render, screen } from '@testing-library/react';" if is_react else ""}
{"import userEvent from '@testing-library/user-event';" if is_react else ""}
// import functions/classes from '../{Path(file_path).name}';

describe('{Path(file_path).stem}', () => {{
'''

        # Add basic test cases
        functions = analysis.get('functions', [])
        classes = analysis.get('classes', [])
        components = analysis.get('components', [])

        for func in functions[:3]:  # Limit for demo
            test_content += f'''
  describe('{func}', () => {{
    it('should be defined', () => {{
      // expect({func}).toBeDefined();
      expect(true).toBe(true); // Placeholder test
    }});

    it('should handle basic functionality', () => {{
      // Add your test logic here
      expect(true).toBe(true);
    }});
  }});'''

        for component in components[:2]:  # Limit for demo
            test_content += f'''

  describe('{component} Component', () => {{
    it('should render without crashing', () => {{
      // render(<{component} />);
      // expect(screen.getByTestId('{component.toLowerCase()}')).toBeInTheDocument();
      expect(true).toBe(true); // Placeholder test
    }});
  }});'''

        test_content += '''
});
'''
        return test_content

    def save_test_file(self, test_content: str, original_file: str):
        """Save generated test file"""
        test_dir = Path('ai-generated-tests')
        test_dir.mkdir(exist_ok=True)

        test_filename = Path(original_file).stem + '.test' + Path(original_file).suffix
        test_path = test_dir / test_filename

        with open(test_path, 'w') as f:
            f.write(test_content)

        print(f"✅ Generated test: {test_path}")

    def run_test_generation(self):
        """Main test generation execution"""
        print("🧪 Starting AI Test Generation...")

        # Find code files to test
        code_extensions = ['*.js', '*.ts', '*.jsx', '*.tsx']
        code_files = []

        for ext in code_extensions:
            code_files.extend(Path('.').glob(f'**/{ext}'))

        # Filter out test files, node_modules, etc.
        code_files = [
            f for f in code_files
            if not str(f).startswith(('node_modules', 'ai-generated-tests'))
            and not f.name.endswith('.test.js') and not f.name.endswith('.test.ts')
            and not f.name.endswith('.spec.js') and not f.name.endswith('.spec.ts')
        ]

        if not code_files:
            print("No code files found to test")
            return

        print(f"📄 Found {len(code_files)} code files to analyze")

        generated_tests = 0
        for file_path in code_files[:3]:  # Limit for demo
            print(f"🔍 Analyzing {file_path}...")

            if file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
                analysis = self.analyze_javascript_file(str(file_path))

                if analysis and any(analysis.values()):  # Only generate if there's something to test
                    print(f"🤖 Generating tests for {file_path}...")
                    test_content = self.generate_tests_with_ai(analysis, str(file_path))
                    self.save_test_file(test_content, str(file_path))
                    generated_tests += 1

        # Create summary
        summary = f"""# 🧪 AI Test Generation Report

## 📊 Summary
- **Files Analyzed:** {len(code_files)}
- **Tests Generated:** {generated_tests}
- **Test Framework:** Vitest
- **Output Directory:** `ai-generated-tests/`

## 📁 Generated Tests

The following test files were created in the `ai-generated-tests/` directory:

"""

        test_dir = Path('ai-generated-tests')
        if test_dir.exists():
            for test_file in test_dir.glob('*.test.*'):
                summary += f"- `{test_file.name}`\n"

        summary += """

## 🚀 Next Steps

1. **Review Generated Tests**: Check the `ai-generated-tests/` directory
2. **Customize Tests**: Modify tests to match your specific requirements
3. **Move Tests**: Copy tests to appropriate `__tests__/` directories
4. **Run Tests**: Execute tests with `npm test`
5. **Fix Issues**: Update tests based on actual implementation

## 💡 Tips

- Tests are generated as templates - customize them for your specific logic
- Add proper mocks for external dependencies
- Include edge cases and error conditions
- Use descriptive test names and assertions

---
*Generated by AI Test Generator*
"""

        with open('ai-test-generation-report.md', 'w') as f:
            f.write(summary)

        print("✅ AI Test Generation completed!")
        print(f"🧪 Generated {generated_tests} test files")
        print("📋 Report saved to ai-test-generation-report.md")

if __name__ == "__main__":
    generator = AITestGenerator()
    generator.run_test_generation()