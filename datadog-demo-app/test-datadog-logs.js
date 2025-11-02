#!/usr/bin/env node

const axios = require('axios');

const DD_API_KEY = 'be9f47b60fedd8042065bd3052eb546e';

async function sendLogToDatadog(message, level = 'info') {
  const logEntry = {
    timestamp: new Date().toISOString(),
    level: level,
    message: message,
    service: 'datadog-demo-app',
    hostname: 'datadog-demo-app',
    ddsource: 'nodejs',
    ddtags: 'env:demo,version:1.0.0',
    user_agent: 'test-script',
    endpoint: '/',
    dd: {
      env: 'demo',
      service: 'datadog-demo-app',
      version: '1.0.0'
    }
  };

  try {
    const response = await axios.post(
      `https://http-intake.logs.datadoghq.com/v1/input/${DD_API_KEY}`,
      logEntry,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    console.log(`✅ Log sent successfully: "${message}"`);
    return response.status;
  } catch (error) {
    console.error(`❌ Failed to send log: ${error.message}`);
    if (error.response) {
      console.error(`Response status: ${error.response.status}`);
      console.error(`Response data:`, error.response.data);
    }
    return false;
  }
}

async function main() {
  console.log('🚀 Testing Datadog log ingestion...');
  console.log(`📡 API Key: ${DD_API_KEY.substring(0, 8)}...`);
  console.log(`🎯 Service: datadog-demo-app`);
  console.log('');

  // Send test logs
  await sendLogToDatadog('Homepage accessed', 'info');
  await sendLogToDatadog('User API called', 'info');
  await sendLogToDatadog('Health check performed', 'info');
  await sendLogToDatadog('Test error occurred', 'error');
  
  console.log('');
  console.log('✅ Test logs sent to Datadog!');
  console.log('🔍 Check your Datadog Log Explorer with filter: service:datadog-demo-app');
  console.log('⏱️  Logs should appear within 1-2 minutes');
}

main().catch(console.error);









