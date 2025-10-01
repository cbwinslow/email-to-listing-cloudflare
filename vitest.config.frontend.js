import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['frontend/src/__tests__/**/*.test.tsx'],
    exclude: ['node_modules/**', 'src/**', 'test/**'],
    setupFiles: ['./frontend/test-setup.ts'],
  },
  esbuild: {
    target: 'node14',
  },
});