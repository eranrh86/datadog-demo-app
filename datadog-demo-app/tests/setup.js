// Test setup file for Jest
const logger = require('../src/utils/logger');

// Mock logger in tests to avoid console spam
jest.mock('../src/utils/logger', () => ({
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  debug: jest.fn(),
  gauge: jest.fn(),
  increment: jest.fn(),
  histogram: jest.fn()
}));

// Global test setup
beforeAll(() => {
  // Set test environment
  process.env.NODE_ENV = 'test';
  process.env.LOG_LEVEL = 'silent';
});

// Clean up after each test
afterEach(() => {
  // Clear all mocks
  jest.clearAllMocks();
});

// Global error handler for unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Increase timeout for flaky tests
jest.setTimeout(15000);
