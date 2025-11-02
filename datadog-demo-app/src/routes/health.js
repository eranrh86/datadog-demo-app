const express = require('express');
const logger = require('../utils/logger');
const { asyncHandler } = require('../middleware/errorHandler');
const router = express.Router();

// Health check endpoint
router.get('/', asyncHandler(async (req, res) => {
  const healthData = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  };

  logger.info('Health check performed', {
    operation: 'health_check',
    status: healthData.status,
    uptime: healthData.uptime,
    memory_usage: healthData.memory.used
  });

  logger.gauge('app.uptime', healthData.uptime);
  logger.gauge('app.memory.used', healthData.memory.used);
  logger.gauge('app.memory.heap_used', healthData.memory.heapUsed);

  res.json(healthData);
}));

// Readiness probe
router.get('/ready', asyncHandler(async (req, res) => {
  // Simulate dependency checks
  const checks = {
    database: await checkDatabase(),
    redis: await checkRedis(),
    external_api: await checkExternalAPI()
  };

  const allHealthy = Object.values(checks).every(check => check.status === 'healthy');
  const overallStatus = allHealthy ? 'ready' : 'not_ready';

  logger.info('Readiness check performed', {
    operation: 'readiness_check',
    overall_status: overallStatus,
    checks: checks
  });

  // Log individual check results
  Object.entries(checks).forEach(([service, check]) => {
    logger.gauge(`app.dependency.${service}.response_time`, check.responseTime);
    logger.increment(`app.dependency.${service}.checks`, 1, {
      status: check.status
    });
  });

  const statusCode = allHealthy ? 200 : 503;
  
  res.status(statusCode).json({
    status: overallStatus,
    timestamp: new Date().toISOString(),
    checks: checks
  });
}));

// Liveness probe
router.get('/live', asyncHandler(async (req, res) => {
  // Simple liveness check
  const isAlive = process.uptime() > 0;
  
  logger.info('Liveness check performed', {
    operation: 'liveness_check',
    status: isAlive ? 'alive' : 'dead',
    uptime: process.uptime()
  });

  if (isAlive) {
    res.json({
      status: 'alive',
      timestamp: new Date().toISOString(),
      uptime: process.uptime()
    });
  } else {
    res.status(503).json({
      status: 'dead',
      timestamp: new Date().toISOString()
    });
  }
}));

// Metrics endpoint for Datadog
router.get('/metrics', asyncHandler(async (req, res) => {
  const metrics = {
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    cpu: process.cpuUsage(),
    version: '1.0.0',
    custom_metrics: {
      active_connections: Math.floor(Math.random() * 100),
      requests_per_minute: Math.floor(Math.random() * 1000),
      error_rate: Math.random() * 0.05, // 0-5% error rate
      response_time_avg: Math.random() * 200 + 50 // 50-250ms
    }
  };

  logger.info('Metrics endpoint accessed', {
    operation: 'metrics_collection',
    uptime: metrics.uptime,
    memory_used: metrics.memory.used
  });

  // Log custom metrics
  Object.entries(metrics.custom_metrics).forEach(([metric, value]) => {
    logger.gauge(`app.${metric}`, value);
  });

  res.json(metrics);
}));

// Simulate dependency checks
async function checkDatabase() {
  const startTime = Date.now();
  
  // Simulate database check with potential failure
  const isHealthy = Math.random() > 0.1; // 90% success rate
  const delay = Math.random() * 100 + 10; // 10-110ms
  
  await new Promise(resolve => setTimeout(resolve, delay));
  
  const responseTime = Date.now() - startTime;
  
  return {
    status: isHealthy ? 'healthy' : 'unhealthy',
    responseTime: responseTime,
    lastChecked: new Date().toISOString(),
    error: isHealthy ? null : 'Connection timeout'
  };
}

async function checkRedis() {
  const startTime = Date.now();
  
  // Simulate Redis check
  const isHealthy = Math.random() > 0.05; // 95% success rate
  const delay = Math.random() * 50 + 5; // 5-55ms
  
  await new Promise(resolve => setTimeout(resolve, delay));
  
  const responseTime = Date.now() - startTime;
  
  return {
    status: isHealthy ? 'healthy' : 'unhealthy',
    responseTime: responseTime,
    lastChecked: new Date().toISOString(),
    error: isHealthy ? null : 'Redis connection failed'
  };
}

async function checkExternalAPI() {
  const startTime = Date.now();
  
  // Simulate external API check with higher failure rate
  const isHealthy = Math.random() > 0.2; // 80% success rate
  const delay = Math.random() * 300 + 50; // 50-350ms
  
  await new Promise(resolve => setTimeout(resolve, delay));
  
  const responseTime = Date.now() - startTime;
  
  return {
    status: isHealthy ? 'healthy' : 'unhealthy',
    responseTime: responseTime,
    lastChecked: new Date().toISOString(),
    error: isHealthy ? null : 'External API unreachable'
  };
}

module.exports = router;
