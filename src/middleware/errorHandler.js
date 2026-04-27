const logger = require('../utils/logger');

const errorHandler = (err, req, res, next) => {
  // Get the active span for Error Tracking
  const tracer = require('dd-trace');
  const span = tracer.scope().active();
  
  // Set error on span for Error Tracking
  if (span) {
    span.setTag('error', true);
    span.setTag('error.type', err.name || 'Error');
    span.setTag('error.message', err.message);
    span.setTag('error.stack', err.stack);
  }
  
  // Log the error with full context for Exception Replay
  logger.error('Unhandled error occurred', {
    error_message: err.message,
    error_stack: err.stack,
    error_name: err.name,
    request_method: req.method,
    request_url: req.url,
    request_headers: req.headers,
    request_body: req.body,
    user_agent: req.get('User-Agent'),
    ip_address: req.ip,
    timestamp: new Date().toISOString(),
    error_type: 'unhandled_exception',
    severity: 'high'
  });

  // Increment error metrics
  logger.increment('app.errors.count', 1, {
    error_type: err.name || 'UnknownError',
    endpoint: req.url,
    method: req.method
  });

  // Determine error response based on environment
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  const errorResponse = {
    error: true,
    message: err.message || 'Internal Server Error',
    timestamp: new Date().toISOString(),
    request_id: req.get('X-Request-ID') || 'unknown'
  };

  // Include stack trace in development
  if (isDevelopment) {
    errorResponse.stack = err.stack;
    errorResponse.details = {
      name: err.name,
      code: err.code,
      statusCode: err.statusCode
    };
  }

  // Determine status code
  const statusCode = err.statusCode || err.status || 500;
  
  res.status(statusCode).json(errorResponse);
};

const notFoundHandler = (req, res, next) => {
  logger.warn('Route not found', {
    method: req.method,
    url: req.url,
    user_agent: req.get('User-Agent'),
    ip_address: req.ip,
    error_type: 'not_found'
  });

  logger.increment('app.errors.not_found', 1, {
    endpoint: req.url,
    method: req.method
  });

  res.status(404).json({
    error: true,
    message: 'Route not found',
    path: req.url,
    method: req.method,
    timestamp: new Date().toISOString()
  });
};

// Async error handler wrapper
const asyncHandler = (fn) => {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

module.exports = {
  errorHandler,
  notFoundHandler,
  asyncHandler
};
