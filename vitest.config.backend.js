import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    include: ['test/**/*.test.js'],
    exclude: ['node_modules/**', 'src/**', 'frontend/**'],
  },
  esbuild: {
    target: 'node14',
    jsx: 'preserve',
  },
});