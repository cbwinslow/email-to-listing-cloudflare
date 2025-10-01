#!/bin/bash

# Automated Testing Framework Setup Script
# This script sets up the comprehensive testing framework for your project

set -e

echo "🚀 Setting up Automated Testing Framework..."

# Check if we're in a Node.js project
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script in your project root."
    exit 1
fi

echo "📦 Installing testing dependencies..."

# Install testing dependencies
npm install --save-dev \
    vitest \
    @testing-library/react \
    @testing-library/jest-dom \
    jsdom \
    jest-axe \
    @playwright/test \
    @vitejs/plugin-react \
    eslint \
    typescript

echo "📋 Updating package.json scripts..."

# Update package.json with test scripts
node -e "
const fs = require('fs');
const package = JSON.parse(fs.readFileSync('package.json', 'utf8'));

package.scripts = package.scripts || {};
package.scripts['test'] = 'vitest --config vitest.config.frontend.js && vitest --config vitest.config.backend.js';
package.scripts['test:frontend'] = 'vitest --config vitest.config.frontend.js';
package.scripts['test:backend'] = 'vitest --config vitest.config.backend.js';
package.scripts['generate-tests'] = 'node test-generator.js';
package.scripts['test:all'] = 'npm run test && npm run test:e2e';
package.scripts['test:e2e'] = 'playwright test';

fs.writeFileSync('package.json', JSON.stringify(package, null, 2));
"

echo "📁 Creating directory structure..."

# Create necessary directories
mkdir -p frontend/src/__tests__
mkdir -p test
mkdir -p .github/workflows

echo "📝 Generating initial tests..."

# Generate tests
npm run generate-tests

echo "🎭 Installing Playwright browsers..."

# Install Playwright browsers
npx playwright install

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Run 'npm test' to execute all tests"
echo "2. Run 'npm run test:e2e' for E2E tests"
echo "3. Check TESTING.md for detailed documentation"
echo "4. Customize test templates in test-generator.js as needed"
echo ""
echo "📊 Your testing framework is ready! 🎉"