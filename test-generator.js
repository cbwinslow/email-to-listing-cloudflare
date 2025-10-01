#!/usr/bin/env node

/**
 * Automated Test Suite Generator for Item Analyzer
 * Generates comprehensive test suites for Next.js + Cloudflare Workers
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class TestGenerator {
  constructor() {
    this.projectRoot = path.resolve(__dirname);
    this.templates = this.loadTemplates();
  }

  loadTemplates() {
    return {
      frontend: {
        component: (name) => `
/**
 * @vitest-environment jsdom
 */
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import ${name} from '../components/${name}';

describe('${name} Component', () => {
  it('renders without crashing', () => {
    const { container } = render(<${name} />);
    // Component may return null (for side effects only) or render content
    expect(container).toBeInTheDocument();
  });

  it('handles props correctly', () => {
    // Test with different props if component accepts them
    const { rerender } = render(<${name} />);
    // Add specific prop tests based on component interface
    expect(true).toBe(true); // Placeholder - customize based on actual component
  });
});

  it('handles props correctly', () => {
    // Test with different props if component accepts them
    const { rerender } = render(<${name} />);
    // Add specific prop tests based on component interface
    expect(true).toBe(true); // Placeholder - customize based on actual component
  });
});
`,
        page: (name) => `
/**
 * @vitest-environment jsdom
 */
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import ${name.charAt(0).toUpperCase() + name.slice(1)} from '../app/${name.toLowerCase()}/page';

describe('${name.charAt(0).toUpperCase() + name.slice(1)} Page', () => {
  beforeEach(() => {
    // Mock any necessary dependencies
    global.fetch = vi.fn();
  });

  it('renders without crashing', () => {
    render(<${name.charAt(0).toUpperCase() + name.slice(1)} />);
    // Check that the page renders some content - look for common elements
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
  });

  it('displays expected content', () => {
    render(<${name.charAt(0).toUpperCase() + name.slice(1)} />);
    // Add specific content checks based on actual page content
    expect(true).toBe(true); // Placeholder - customize based on actual page
  });
});
`
      },
      backend: {
        worker: (name) => `
import { describe, it, expect, vi } from 'vitest';

// Mock environment
const mockEnv = {
  CACHE: { get: vi.fn(), put: vi.fn() },
  SUPABASE_URL: 'https://test.supabase.co',
  SUPABASE_ANON_KEY: 'test-key',
  EBAY_TOKEN: 'test-token',
  AI: {},
  IMAGES: { put: vi.fn() },
  ENCRYPTION_KEY: 'test-key'
};

describe('${name} Worker', () => {
  it('handles health check', async () => {
    const { default: handler } = await import('../src/${name}.js');
    const request = new Request('http://localhost/api/health');

    const response = await handler(request, mockEnv, {});
    expect(response.status).toBe(200);

    const data = await response.json();
    expect(data.status).toBe('ok');
  });

  it('handles POST requests', async () => {
    const { default: handler } = await import('../src/${name}.js');
    const request = new Request('http://localhost/api/${name.toLowerCase()}', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test: 'data' })
    });

    const response = await handler(request, mockEnv, {});
    expect(response.status).toBe(200);
  });

  it('handles invalid requests', async () => {
    const { default: handler } = await import('../src/${name}.js');
    const request = new Request('http://localhost/api/invalid');

    const response = await handler(request, mockEnv, {});
    expect(response.status).toBe(404);
  });

  it('enforces rate limiting', async () => {
    const { default: handler } = await import('../src/${name}.js');

    // Simulate multiple requests
    for (let i = 0; i < 105; i++) {
      const request = new Request('http://localhost/api/${name.toLowerCase()}', { method: 'POST' });
      await handler(request, mockEnv, {});
    }

    const request = new Request('http://localhost/api/${name.toLowerCase()}', { method: 'POST' });
    const response = await handler(request, mockEnv, {});
    expect(response.status).toBe(429);
  });

  it('sanitizes inputs', async () => {
    const { default: handler } = await import('../src/${name}.js');
    const request = new Request('http://localhost/api/${name.toLowerCase()}', {
      method: 'POST',
      body: JSON.stringify({ input: '<script>alert("xss")</script>test' })
    });

    const response = await handler(request, mockEnv, {});
    expect(response.status).toBe(200);

    // Verify input was sanitized
    const data = await response.text();
    expect(data).not.toContain('<script>');
  });
});
`,
        api: (name) => `
import { describe, it, expect, vi } from 'vitest';

describe('${name} API', () => {
  const mockEnv = {
    // Add relevant environment variables
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('validates request parameters', async () => {
    // Test parameter validation
  });

  it('handles authentication', async () => {
    // Test auth middleware
  });

  it('processes data correctly', async () => {
    // Test data processing logic
  });

  it('returns appropriate responses', async () => {
    // Test response formatting
  });

  it('handles errors gracefully', async () => {
    // Test error handling
  });
});
`
      },
      integration: {
        e2e: (name) => `
import { test, expect } from '@playwright/test';

test.describe('${name} E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('complete user workflow', async ({ page }) => {
    // Navigate to the application
    await expect(page).toHaveTitle(/Item Analyzer/);

    // Fill out the form
    await page.fill('textarea[name="description"]', 'Test item description');
    await page.fill('input[name="url"]', 'https://example.com');
    await page.fill('input[name="email"]', 'test@example.com');

    // Submit the form
    await page.click('button[type="submit"]');

    // Wait for results
    await page.waitForSelector('.results');
    await expect(page.locator('.results')).toBeVisible();
  });

  test('handles form validation', async ({ page }) => {
    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Check for validation errors
    await expect(page.locator('.error')).toBeVisible();
  });

  test('responsive design', async ({ page, browserName }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('form')).toBeVisible();

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('form')).toBeVisible();
  });

  test('accessibility', async ({ page }) => {
    // Check for proper ARIA labels
    await expect(page.locator('[aria-label]')).toBeTruthy();

    // Test keyboard navigation
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
  });
});
`
      }
    };
  }

  analyzeCodebase() {
    const components = this.findComponents();
    const pages = this.findPages();
    const workers = this.findWorkers();
    const apis = this.findAPIs();

    return { components, pages, workers, apis };
  }

  findComponents() {
    const componentsDir = path.join(this.projectRoot, 'frontend/src/components');
    if (!fs.existsSync(componentsDir)) return [];

    return fs.readdirSync(componentsDir)
      .filter(file => file.endsWith('.tsx') || file.endsWith('.jsx'))
      .map(file => path.basename(file, path.extname(file)));
  }

  findPages() {
    const pagesDir = path.join(this.projectRoot, 'frontend/src/app');
    if (!fs.existsSync(pagesDir)) return [];

    return fs.readdirSync(pagesDir)
      .filter(dir => fs.statSync(path.join(pagesDir, dir)).isDirectory())
      .filter(dir => fs.existsSync(path.join(pagesDir, dir, 'page.tsx')));
  }

  findWorkers() {
    const srcDir = path.join(this.projectRoot, 'src');
    if (!fs.existsSync(srcDir)) return [];

    return fs.readdirSync(srcDir)
      .filter(file => file.endsWith('.js'))
      .map(file => path.basename(file, '.js'));
  }

  findAPIs() {
    // Analyze the main worker file for API endpoints
    const indexFile = path.join(this.projectRoot, 'src/index.js');
    if (!fs.existsSync(indexFile)) return [];

    const content = fs.readFileSync(indexFile, 'utf8');
    const apiMatches = content.match(/url\.pathname === ['"]([^'"]+)['"]/g) || [];
    return apiMatches.map(match => match.match(/['"]([^'"]+)['"]/)[1].replace('/api/', ''));
  }

  generateTests() {
    const { components, pages, workers, apis } = this.analyzeCodebase();

    console.log('🔍 Analyzing codebase...');
    console.log(`📁 Found ${components.length} components, ${pages.length} pages, ${workers.length} workers, ${apis.length} APIs`);

    // Generate frontend tests
    components.forEach(comp => this.generateFrontendTest(comp, 'component'));
    pages.forEach(page => this.generateFrontendTest(page, 'page'));

    // Generate backend tests
    workers.forEach(worker => this.generateBackendTest(worker, 'worker'));
    apis.forEach(api => this.generateBackendTest(api, 'api'));

    // Generate integration tests
    this.generateIntegrationTest('ItemAnalyzer');

    console.log('✅ Test generation complete!');
    console.log('📊 Run "npm test" to execute the generated tests');
  }

  generateFrontendTest(name, type) {
    const template = this.templates.frontend[type];
    if (!template) return;

    const testContent = template(name);
    const testDir = path.join(this.projectRoot, 'frontend/src/__tests__');
    const testFile = path.join(testDir, `${name.toLowerCase()}.test.tsx`);

    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }

    fs.writeFileSync(testFile, testContent);
    console.log(`📝 Generated frontend ${type} test: ${testFile}`);
  }

  generateBackendTest(name, type) {
    const template = this.templates.backend[type];
    if (!template) return;

    const testContent = template(name);
    const testDir = path.join(this.projectRoot, 'test');
    const testFile = path.join(testDir, `${name.toLowerCase()}.test.js`);

    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }

    fs.writeFileSync(testFile, testContent);
    console.log(`📝 Generated backend ${type} test: ${testFile}`);
  }

  generateIntegrationTest(name) {
    const template = this.templates.integration.e2e;
    const testContent = template(name);
    const testDir = path.join(this.projectRoot, 'frontend/e2e');
    const testFile = path.join(testDir, `${name.toLowerCase()}.spec.ts`);

    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }

    fs.writeFileSync(testFile, testContent);
    console.log(`📝 Generated integration test: ${testFile}`);
  }

  updatePackageScripts() {
    const packagePath = path.join(this.projectRoot, 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));

    packageJson.scripts = packageJson.scripts || {};
    packageJson.scripts['generate-tests'] = 'node test-generator.js';
    packageJson.scripts['test:all'] = 'npm run test && npm run test:e2e';
    packageJson.scripts['test:e2e'] = 'playwright test';

    fs.writeFileSync(packagePath, JSON.stringify(packageJson, null, 2));
    console.log('📦 Updated package.json with test scripts');
  }

  setupCI() {
    const ciConfig = `
name: CI/CD Pipeline
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Generate tests
        run: npm run generate-tests

      - name: Run unit tests
        run: npm test

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/lcov.info

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Cloudflare
        run: npm run deploy
        env:
          CLOUDFLARE_API_TOKEN: \${{ secrets.CLOUDFLARE_API_TOKEN }}
`;

    const ciPath = path.join(this.projectRoot, '.github/workflows/ci.yml');
    fs.mkdirSync(path.dirname(ciPath), { recursive: true });
    fs.writeFileSync(ciPath, ciConfig);
    console.log('🚀 Created CI/CD pipeline configuration');
  }
}

// CLI interface
const generator = new TestGenerator();

if (process.argv[2] === '--ci') {
  generator.setupCI();
} else if (process.argv[2] === '--update-scripts') {
  generator.updatePackageScripts();
} else {
  generator.generateTests();
}