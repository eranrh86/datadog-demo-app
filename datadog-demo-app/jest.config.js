module.exports = {
  testEnvironment: 'node',
  testMatch: [
    '**/tests/**/*.test.js',
    '**/__tests__/**/*.js'
  ],
  // Exclude Playwright spec files — those run via playwright CLI, not Jest
  testPathIgnorePatterns: [
    '/node_modules/',
    '\\.spec\\.js$',
    '/tests/auth/',
    '/tests/mobile/',
  ],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/app.js', // Exclude main app file from coverage
    '!**/node_modules/**'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',
    'lcov',
    'html'
  ],
  coverageThreshold: {
    global: {
      branches: 50,
      functions: 60,
      lines: 60,
      statements: 60,
    },
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  testTimeout: 10000,
  verbose: true,
  maxWorkers: 1, // Run tests sequentially to avoid race conditions
  forceExit: true,
  clearMocks: true,
  restoreMocks: true,
  // Map module names for easier imports in tests
  moduleNameMapper: {
    '^@fixtures/(.*)$': '<rootDir>/tests/fixtures/$1',
    '^@src/(.*)$': '<rootDir>/src/$1',
  },
};
