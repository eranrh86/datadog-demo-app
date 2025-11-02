// Simple test script to verify the demo app works locally
const http = require('http');

// Test the application
function testEndpoint(path, description) {
  return new Promise((resolve) => {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: path,
      method: 'GET'
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        console.log(`✅ ${description}: ${res.statusCode}`);
        if (res.statusCode === 200) {
          console.log(`   Response: ${data.substring(0, 100)}...`);
        }
        resolve();
      });
    });

    req.on('error', (err) => {
      console.log(`❌ ${description}: ${err.message}`);
      resolve();
    });

    req.setTimeout(5000, () => {
      console.log(`⏰ ${description}: Timeout`);
      req.destroy();
      resolve();
    });

    req.end();
  });
}

async function runTests() {
  console.log('🧪 Testing Datadog Demo App...\n');
  
  const tests = [
    ['/', 'Homepage'],
    ['/api/health', 'Health Check'],
    ['/api/users', 'Users API'],
    ['/api/orders', 'Orders API'],
    ['/api/users/999', 'Runtime Error (expected)'],
    ['/vulnerable/123', 'Security Vulnerability'],
    ['/error/runtime', 'Exception Replay']
  ];

  for (const [path, description] of tests) {
    await testEndpoint(path, description);
    await new Promise(resolve => setTimeout(resolve, 500)); // Small delay
  }

  console.log('\n🎯 Demo app testing complete!');
  console.log('If you see ✅ responses, your app is working correctly.');
  console.log('Now you can proceed with your Datadog demo tomorrow!');
}

runTests();

