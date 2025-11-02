const logger = require('../utils/logger');

const requestLogger = (req, res, next) => {
  const startTime = Date.now();
  
  // Log request start
  logger.info('Request started', {
    method: req.method,
    url: req.url,
    user_agent: req.get('User-Agent'),
    ip_address: req.ip,
    request_id: req.get('X-Request-ID') || generateRequestId(),
    timestamp: new Date().toISOString()
  });

  // Capture response
  const originalSend = res.send;
  res.send = function(data) {
    const duration = Date.now() - startTime;
    
    // Log request completion with metrics
    logger.info('Request completed', {
      method: req.method,
      url: req.url,
      status_code: res.statusCode,
      response_time: duration,
      content_length: data ? data.length : 0,
      request_id: req.get('X-Request-ID') || 'unknown'
    });

    // Log volume and performance metrics
    logger.gauge('http.request.duration', duration, {
      method: req.method,
      status_code: res.statusCode.toString(),
      endpoint: req.route?.path || req.url
    });

    logger.increment('http.request.count', 1, {
      method: req.method,
      status_code: res.statusCode.toString(),
      endpoint: req.route?.path || req.url
    });

    return originalSend.call(this, data);
  };

  next();
};

function generateRequestId() {
  return Math.random().toString(36).substr(2, 9);
}

module.exports = { requestLogger };
