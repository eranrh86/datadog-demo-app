// Force service name in environment for Datadog extension
process.env.DD_SERVICE = process.env.DD_SERVICE || 'datadog-demo-app';
process.env.DD_ENV = process.env.DD_ENV || 'demo';
process.env.DD_VERSION = process.env.DD_VERSION || '1.0.0';

// Set Git metadata for source code integration
process.env.DD_GIT_REPOSITORY_URL = process.env.DD_GIT_REPOSITORY_URL || 'https://github.com/eranrh86/datadog-demo-app';
if (!process.env.DD_GIT_COMMIT_SHA) {
  try {
    process.env.DD_GIT_COMMIT_SHA = require('child_process').execSync('git rev-parse HEAD 2>/dev/null', { encoding: 'utf8' }).trim();
  } catch {
    process.env.DD_GIT_COMMIT_SHA = '';
  }
}

// Initialize Datadog tracer FIRST with Error Tracking and LLM Observability enabled
const tracer = require('dd-trace').init({
  service: 'datadog-demo-app',
  env: 'demo',
  version: '1.0.0',
  logInjection: true,
  runtimeMetrics: true,
  profiling: true,
  // Enable Error Tracking for Code Insights
  appsec: {
    enabled: false // We don't need AppSec, just Error Tracking
  }
});

// Initialize LLM Observability only when DD_API_KEY is set (optional)
const { llmobs } = tracer;
if (llmobs && process.env.DD_API_KEY) {
  llmobs.enable({
    mlApp: 'datadog-demo-app',
    agentlessEnabled: true
  });
}

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const logger = require('./utils/logger');
const userRoutes = require('./routes/users');
const orderRoutes = require('./routes/orders');
const healthRoutes = require('./routes/health');
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');
const { requestLogger } = require('./middleware/requestLogger');

// TEST ERROR: This will cause a runtime error for Fix in Chat demo
// TODO: Fix this undefined variable reference
// TEMPORARILY COMMENTED OUT FOR E-COMMERCE DEMO
// const testConfig = undefinedVariable.someProperty;

const app = express();
const PORT = process.env.PORT || 3000;
const path = require('path');

// Security middleware
app.use(helmet({
  contentSecurityPolicy: false, // Disable for demo to allow inline scripts
}));

// CONFIGURATION ISSUE: Insecure CORS configuration
app.use(cors({
  origin: '*', // Allows any origin - security risk!
  credentials: true // Dangerous when combined with origin: '*'
}));

// Serve static files
app.use(express.static(path.join(__dirname, '../public')));

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// TEST ERROR 1: Deprecated API usage
const crypto = require('crypto');
const _hash = crypto.createHash('md5'); // MD5 deprecated - demo only

// TEST ERROR 2: Hardcoded credentials (demo only)
const _API_KEY = 'sk_test_1234567890abcdef';
const _DATABASE_PASSWORD = 'admin123';

// CONFIGURATION ISSUE: Insecure TLS (demo only)
const _https = require('https');
const _tlsOptions = {
  minVersion: 'TLSv1', // Insecure - should use TLSv1.2 or higher
  ciphers: 'RC4', // Weak cipher
  rejectUnauthorized: false // Disables certificate validation - dangerous!
};

// Request logging middleware
app.use(requestLogger);

// Routes
const chatbotRoutes = require('./routes/chatbot');
const checkoutRoutes = require('./routes/checkout');
app.use('/api/health', healthRoutes);
app.use('/api/users', userRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/checkout', checkoutRoutes);
app.use('/api/chatbot', chatbotRoutes);

// API info endpoint
app.get('/api', (req, res) => {
  const span = tracer.scope().active();

  // TEST ERROR 3: Using == instead of ===
  if (req.query.debug === 'true') {
    logger.debug('Debug mode'); // Fixed: Using proper logger instead of console.log
  }

  // Log annotation example - gauge log volumes
  logger.info('API info accessed', {
    dd: {
      trace_id: span?.context()?.toTraceId(),
      span_id: span?.context()?.toSpanId(),
    },
    user_agent: req.get('User-Agent'),
    ip_address: req.ip,
    endpoint: '/api',
    log_volume_gauge: 1
  });

  res.json({
    message: 'Welcome to Datadog Demo App API',
    timestamp: new Date().toISOString(),
    features: [
      'Log Annotations',
      'Code Insights',
      'View in IDE',
      'Static Code Analysis',
      'Exception Replay',
      'Fix in Chat'
    ]
  });
});

// VULNERABILITY: SQL Injection vulnerability for demo
app.get('/vulnerable/:id', (req, res) => {
  const { id } = req.params;

  // VULNERABILITY: SQL Injection - using string concatenation instead of parameterized query
  const query = 'SELECT * FROM users WHERE id = ' + id; // Dangerous!

  // VULNERABILITY: Using eval with user input (intentional for security demo)
  const userInput = req.query.calc || '2+2';
  // eslint-disable-next-line no-eval, security/detect-eval-with-expression
  const result = eval(userInput);

  logger.warn('Vulnerable endpoint accessed', {
    user_id: id,
    query: query,
    security_risk: 'HIGH - SQL Injection & Code Injection',
    user_input: userInput
  });

  res.json({
    message: `User ID: ${id}`,
    result: result,
    warning: 'This endpoint has SQL injection and eval vulnerabilities',
    query: query
  });
});

// Runtime error endpoint for Exception Replay
app.get('/error/runtime', (req, res) => {
  logger.error('Intentional runtime error triggered for demo');

  // This will cause a runtime error
  const undefinedObject = null;
  const result = undefinedObject.someProperty.anotherProperty;

  res.json({ result });
});

// Memory leak simulation for Code Insights (SAFE VERSION)
app.get('/memory-leak', (req, res) => {
  const leakyArray = [];

  // TEST ERROR 5: Missing await for async operation (demo)
  const _data = Promise.resolve({ value: 123 });

  // TEST ERROR 6: Unused variable (demo)
  const _unusedVariable = 'This is never used';

  // SAFE: Only create a small leak, then stop (not infinite)
  let count = 0;
  const leakInterval = setInterval(() => {
    leakyArray.push(new Array(10000).fill('memory leak data'));
    count++;
    if (count >= 5) {
      clearInterval(leakInterval); // Stop after 5 iterations
    }
  }, 100);

  logger.warn('Memory leak endpoint triggered (safe version)', {
    memory_usage: process.memoryUsage(),
    leak_simulation: true,
    max_iterations: 5
  });

  res.json({
    message: 'Memory leak simulation started (safe version)',
    note: 'Will stop after 5 iterations to prevent crash'
  });
});

// Error handlers
app.use(notFoundHandler);
app.use(errorHandler);

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

// Only start server if not in test environment
if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => {
    logger.info(`Server started on port ${PORT}`, {
      port: PORT,
      environment: process.env.NODE_ENV || 'development',
      datadog_service: 'datadog-demo-app'
    });
  });
}

module.exports = app;
