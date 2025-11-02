// Force service name in environment for Datadog extension
process.env.DD_SERVICE = process.env.DD_SERVICE || 'datadog-demo-app';
process.env.DD_ENV = process.env.DD_ENV || 'demo';
process.env.DD_VERSION = process.env.DD_VERSION || '1.0.0';

// Initialize Datadog tracer FIRST with Error Tracking enabled
const tracer = require('dd-trace').init({
  service: 'datadog-demo-app',
  env: 'demo',
  version: '1.0.0',
  logInjection: true,
  runtimeMetrics: true,
  profiling: true,
  // Enable Error Tracking for Code Insights
  appsec: {
    enabled: false  // We don't need AppSec, just Error Tracking
  }
});

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const logger = require('./utils/logger');
const userRoutes = require('./routes/users');
const orderRoutes = require('./routes/orders');
const healthRoutes = require('./routes/health');
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');
const { requestLogger } = require('./middleware/requestLogger');

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet());
app.use(cors());

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use(requestLogger);

// Routes
app.use('/api/health', healthRoutes);
app.use('/api/users', userRoutes);
app.use('/api/orders', orderRoutes);

// Root endpoint with log annotations
app.get('/', (req, res) => {
  const span = tracer.scope().active();
  
  // Log annotation example - gauge log volumes
  logger.info('Homepage accessed', {
    dd: {
      trace_id: span?.context()?.toTraceId(),
      span_id: span?.context()?.toSpanId(),
    },
    user_agent: req.get('User-Agent'),
    ip_address: req.ip,
    endpoint: '/',
    log_volume_gauge: 1
  });

  res.json({
    message: 'Welcome to Datadog Demo App',
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

// Intentional vulnerability for Code Insights demo
app.get('/vulnerable/:id', (req, res) => {
  const { id } = req.params;
  
  // VULNERABILITY: SQL Injection potential
  const query = `SELECT * FROM users WHERE id = ${id}`;
  
  // VULNERABILITY: Eval usage
  const result = eval(`"User ID: ${id}"`);
  
  logger.warn('Vulnerable endpoint accessed', {
    user_id: id,
    query: query,
    security_risk: 'high'
  });

  res.json({ 
    message: result,
    warning: 'This endpoint has intentional vulnerabilities for demo purposes'
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

// Memory leak simulation for Code Insights
app.get('/memory-leak', (req, res) => {
  const leakyArray = [];
  
  // Intentional memory leak
  setInterval(() => {
    leakyArray.push(new Array(1000000).fill('memory leak data'));
  }, 100);

  logger.warn('Memory leak endpoint triggered', {
    memory_usage: process.memoryUsage(),
    leak_simulation: true
  });

  res.json({ message: 'Memory leak simulation started' });
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
