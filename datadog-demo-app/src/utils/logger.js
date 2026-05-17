const winston = require('winston');
const tracer = require('dd-trace');

// Custom log format for Datadog integration
const logFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    // Get current trace context from dd-trace
    const span = tracer.scope().active();
    const traceId = span?.context()?.toTraceId();
    const spanId = span?.context()?.toSpanId();

    // Map winston log level to Datadog status
    const statusMap = {
      error: 'error',
      warn: 'warning',
      info: 'info',
      http: 'info',
      debug: 'debug'
    };
    const status = statusMap[level] || 'info';

    return JSON.stringify({
      timestamp,
      level,
      message,
      status, // Add status field for Datadog filtering
      service: 'datadog-demo-app',
      host: process.env.HOSTNAME || 'localhost',
      dd: {
        trace_id: traceId,
        span_id: spanId,
        env: 'demo',
        service: 'datadog-demo-app',
        version: '1.0.0'
      },
      ...meta
    });
  })
);

// Create transports array
const transports = [
  // Console transport — JSON format so Datadog agent can parse stdout
  new winston.transports.Console(),
  
  // File transport for production logs
  new winston.transports.File({
    filename: 'logs/error.log',
    level: 'error',
    maxsize: 5242880, // 5MB
    maxFiles: 5
  }),
  
  // Combined log file
  new winston.transports.File({
    filename: 'logs/combined.log',
    maxsize: 5242880, // 5MB
    maxFiles: 5
  })
];

// Add Datadog HTTP transport if API key is available
if (process.env.DD_API_KEY) {
  try {
    const axios = require('axios');
    
    // Custom Datadog HTTP transport that sends logs via HTTP
    class DatadogHttpTransport extends winston.Transport {
      constructor(options) {
        super(options);
        this.name = 'datadog-http';
        this.apiKey = options.apiKey;
        this.service = options.service || 'datadog-demo-app';
        this.hostname = options.hostname || 'localhost';
        this.ddsource = options.ddsource || 'nodejs';
        this.ddtags = options.ddtags || 'env:demo,version:1.0.0';
      }

      log(info, callback) {
        // Parse the JSON message to merge with log entry
        let logData = {};
        try {
          if (typeof info.message === 'string' && info.message.startsWith('{')) {
            logData = JSON.parse(info.message);
          }
        } catch (e) {
          // Message is not JSON, keep it as is
        }

        // Map winston log level to Datadog status
        const statusMap = {
          error: 'error',
          warn: 'warning',
          info: 'info',
          http: 'info',
          debug: 'debug'
        };
        const status = statusMap[info.level] || 'info';

        const logEntry = {
          message: info.message,
          level: info.level,
          status: status, // Add explicit status field
          service: this.service,
          hostname: this.hostname,
          ddsource: this.ddsource,
          ddtags: this.ddtags,
          timestamp: new Date().toISOString(),
          ...logData,
          // Ensure dd context is always present
          dd: {
            trace_id: logData.dd?.trace_id,
            span_id: logData.dd?.span_id,
            env: 'demo',
            service: 'datadog-demo-app',
            version: '1.0.0'
          }
        };

        // Send to Datadog HTTP logs intake
        axios.post('https://http-intake.logs.datadoghq.com/v1/input/' + this.apiKey, logEntry, {
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 5000
        }).catch(error => {
          console.error('❌ Failed to send log to Datadog:', error.message);
        });

        callback();
      }
    }

    transports.push(new DatadogHttpTransport({
      apiKey: process.env.DD_API_KEY,
      hostname: 'datadog-demo-app',
      service: 'datadog-demo-app',
      ddsource: 'nodejs',
      ddtags: 'env:demo,version:1.0.0'
    }));
    
    console.log('✅ Datadog HTTP transport configured');
  } catch (error) {
    console.log('⚠️ Datadog transport not available:', error.message);
  }
} else {
  console.log('⚠️ DD_API_KEY not set - logs will only go to files');
}

// Create logger with multiple transports
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: {
    service: 'datadog-demo-app',
    environment: process.env.NODE_ENV || 'development'
  },
  transports: transports,
  
  // Handle uncaught exceptions
  exceptionHandlers: [
    new winston.transports.File({ filename: 'logs/exceptions.log' })
  ],
  
  // Handle unhandled promise rejections
  rejectionHandlers: [
    new winston.transports.File({ filename: 'logs/rejections.log' })
  ]
});

// Add custom methods for log annotations
logger.gauge = (metric, value, tags = {}) => {
  logger.info('Metric gauge', {
    metric_type: 'gauge',
    metric_name: metric,
    metric_value: value,
    tags: tags,
    dd_custom_metric: true
  });
};

logger.increment = (metric, value = 1, tags = {}) => {
  logger.info('Metric increment', {
    metric_type: 'increment',
    metric_name: metric,
    metric_value: value,
    tags: tags,
    dd_custom_metric: true
  });
};

logger.histogram = (metric, value, tags = {}) => {
  logger.info('Metric histogram', {
    metric_type: 'histogram',
    metric_name: metric,
    metric_value: value,
    tags: tags,
    dd_custom_metric: true
  });
};

// Log volume tracking
let logVolumeCounter = 0;
const originalLog = logger.log;
logger.log = function(level, message, meta) {
  logVolumeCounter++;
  
  // Emit log volume gauge every 100 logs
  if (logVolumeCounter % 100 === 0) {
    this.gauge('app.log_volume', logVolumeCounter, {
      service: 'datadog-demo-app',
      level: level
    });
  }
  
  return originalLog.call(this, level, message, {
    ...meta,
    log_sequence: logVolumeCounter
  });
};

module.exports = logger;
