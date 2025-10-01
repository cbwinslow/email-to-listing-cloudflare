# 🚀 Automated Testing Framework Template

[![Test Status](https://github.com/cbwinslow/automated-testing-framework-template/actions/workflows/test-template.yml/badge.svg)](https://github.com/cbwinslow/automated-testing-framework-template/actions/workflows/test-template.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **One-command testing setup for React/Next.js + Cloudflare Workers projects**

A comprehensive, automated testing framework that generates 20+ tests instantly for your modern web applications. Built with the latest testing technologies and designed for developer productivity.

## ✨ Features

### 🤖 Automated Test Generation
- **Zero-config setup**: Run one command, get comprehensive test coverage
- **Smart analysis**: Automatically scans your codebase and generates appropriate tests
- **Template system**: Reusable test patterns for consistent testing

### 🧪 Complete Testing Stack
- **Unit Tests**: React components and Cloudflare Workers
- **Integration Tests**: API endpoints and data flow
- **E2E Tests**: Playwright-powered end-to-end testing
- **Accessibility Tests**: Automated a11y compliance with Jest Axe

### ⚡ Modern Technologies
- **Vitest**: Lightning-fast test runner
- **Testing Library**: User-centric testing utilities
- **Playwright**: Cross-browser E2E testing
- **Jest Axe**: Accessibility testing

### 🚀 CI/CD Ready
- **GitHub Actions**: Automated test generation and execution
- **Multi-environment**: Test across Node.js versions
- **Coverage reports**: Codecov integration
- **Security scanning**: Automated vulnerability checks

### 🤖 AI-Powered Analysis
- **CrewAI Orchestration**: Multi-agent AI analysis system
- **Code Review**: Automated bug detection and improvement suggestions
- **Documentation Generation**: AI-powered README and API docs
- **Refactoring Analysis**: Complexity analysis and improvement recommendations
- **Security Auditing**: Automated vulnerability assessment
- **Architecture Review**: System design and scalability analysis

## 📦 Quick Start

### Use This Template

1. **Click "Use this template"** on GitHub
2. **Clone your new repository**
3. **Run the setup script**:

```bash
# Make setup script executable and run it
chmod +x setup.sh
./setup.sh
```

That's it! Your project now has comprehensive test coverage.

### AI-Powered Analysis

For advanced AI analysis, set up these secrets in your repository:

```bash
# OpenRouter API Key (for cloud AI models)
OPENROUTER_API_KEY=your_openrouter_key

# LocalAI Base URL (for local AI models)
LOCALAI_BASE_URL=http://your-localai-server:8080
```

Then trigger AI analysis:

```bash
# Run comprehensive AI analysis
gh workflow run crewai-orchestration.yml

# Run AI code review on PR
# (Automatically triggered on PR creation)
```

### Manual Installation

If you prefer manual setup:

## 🎯 What You Get

### Generated Test Coverage
- ✅ **Component Tests**: Renders, props, interactions, accessibility
- ✅ **Page Tests**: Content rendering, user workflows
- ✅ **API Tests**: Endpoints, validation, error handling, security
- ✅ **E2E Tests**: Complete user journeys across browsers

### AI-Powered Analysis Suite
- 🤖 **CrewAI Orchestration**: Multi-agent AI analysis system
- 🔍 **Code Review**: Automated bug detection and security analysis
- 📚 **Documentation**: AI-generated README and API documentation
- 🔄 **Refactoring**: Complexity analysis and improvement suggestions
- 🛡️ **Security Audit**: Automated vulnerability assessment
- 🏗️ **Architecture Review**: System design and scalability analysis

### Example Generated Tests

**Component Test** (`Button.test.tsx`):
```typescript
describe('Button Component', () => {
  it('renders without crashing', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click me</Button>);

    await userEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
```

**Page Test** (`HomePage.test.tsx`):
```typescript
describe('HomePage', () => {
  it('renders page title', () => {
    render(<HomePage />);
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
  });

  it('displays expected content', () => {
    render(<HomePage />);
    expect(screen.getByText('Welcome')).toBeInTheDocument();
  });
});
```

## 🏗️ Project Structure

```
your-project/
├── test-generator.js          # Core test generation engine
├── vitest.config.frontend.js  # Frontend testing configuration
├── vitest.config.backend.js   # Backend testing configuration
├── test-setup.ts              # Test environment setup
├── TESTING.md                 # Comprehensive testing guide
├── .github/
│   └── workflows/             # CI/CD workflows
├── frontend/src/__tests__/    # Generated component/page tests
├── test/                      # Generated API/worker tests
└── frontend/e2e/              # Generated E2E tests
```

## 🛠️ Customization

### Modify Test Templates

Edit `test-generator.js` to customize generated tests:

```javascript
// Customize component test template
component: (name) => `
describe('${name} Component', () => {
  it('renders with required props', () => {
    render(<${name} requiredProp="value" />);
    expect(screen.getByTestId('${name.toLowerCase()}')).toBeInTheDocument();
  });

  it('handles user interactions', async () => {
    // Your custom interaction tests
  });
});
`
```

### Configure Test Generation

Modify `test-automation-config.json`:

```json
{
  "frontend": {
    "components": true,
    "pages": true,
    "accessibility": true
  },
  "backend": {
    "workers": true,
    "apis": true,
    "security": true
  },
  "e2e": {
    "enabled": true,
    "browsers": ["chromium", "firefox", "webkit"]
  }
}
```

## 📊 CI/CD Integration

### GitHub Actions Workflows

The template includes automated workflows for:

#### Core Testing
- **Test Generation**: Auto-generates tests when code changes
- **Multi-Node Testing**: Tests across Node.js versions
- **Security Audits**: Automated vulnerability scanning
- **Performance Testing**: Lighthouse CI integration
- **Coverage Reports**: Codecov integration

#### AI-Powered Analysis
- **AI Code Review**: Automated code analysis on PRs
- **CrewAI Orchestration**: Multi-agent AI analysis system
- **Documentation Review**: AI-powered documentation generation
- **Refactoring Analysis**: Automated improvement suggestions

### Using AI Workflows

#### Manual AI Analysis
```bash
# Trigger comprehensive AI analysis
gh workflow run crewai-orchestration.yml

# Run specific analysis types
gh workflow run crewai-orchestration.yml -f analysis_type=security-audit
gh workflow run crewai-orchestration.yml -f analysis_type=refactoring-analysis
```

#### Automatic AI Analysis
- **On PR Creation**: AI code review automatically runs
- **Weekly Schedule**: Comprehensive analysis every Monday
- **Manual Trigger**: Run anytime via GitHub Actions

#### AI Analysis Results
- 📄 **Reports**: Generated in `ai-*.md` and `crewai-*.md` files
- 💬 **PR Comments**: AI suggestions posted as PR comments
- 📊 **Artifacts**: Analysis results saved for 30 days

### Example Workflow

```yaml
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run generate-tests  # Auto-generate tests
      - run: npm test               # Run all tests
      - run: npm run test:e2e       # Run E2E tests
```

## 🎨 Technology Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| **Vitest** | Test runner | ^3.2.4 |
| **@testing-library/react** | React testing | ^16.3.0 |
| **@testing-library/jest-dom** | DOM assertions | ^6.9.0 |
| **jsdom** | DOM environment | ^27.0.0 |
| **jest-axe** | Accessibility testing | ^10.0.0 |
| **@playwright/test** | E2E testing | ^1.55.1 |

## 📈 Scaling

### For Large Projects
- **Monorepo Support**: Works with multiple packages
- **Custom Templates**: Project-specific test patterns
- **Parallel Testing**: Split tests across multiple runners
- **Shared Configurations**: Common testing setup

### Enterprise Integration
- **SSO Integration**: Connect with enterprise auth
- **Custom Reporting**: Integration with test management tools
- **Compliance**: SOX, HIPAA, GDPR test requirements
- **Performance**: Large-scale test execution

## 🤝 Contributing

1. **Fork** this template repository
2. **Create** a feature branch
3. **Add** your improvements
4. **Test** thoroughly
5. **Submit** a pull request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/cbwinslow/automated-testing-framework-template.git
cd automated-testing-framework-template
npm install
npm test
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Vitest Team** for the amazing test runner
- **Testing Library** for user-centric testing philosophy
- **Playwright** for reliable E2E testing
- **Jest Axe** for accessibility testing

## 📞 Support

- 📖 **Documentation**: [TESTING.md](TESTING.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/cbwinslow/automated-testing-framework-template/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/cbwinslow/automated-testing-framework-template/discussions)

---

**Ready to supercharge your testing? Click "Use this template" and get comprehensive test coverage in minutes! 🚀**