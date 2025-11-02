const request = require('supertest');
const app = require('../src/app');

describe('Orders API', () => {
  test('should get all orders', async () => {
    const response = await request(app)
      .get('/api/orders')
      .expect(200);

    expect(response.body).toHaveProperty('orders');
    expect(Array.isArray(response.body.orders)).toBe(true);
    expect(response.body).toHaveProperty('fetch_duration');
  });

  test('should get order by ID', async () => {
    const response = await request(app)
      .get('/api/orders/1')
      .expect(200);

    expect(response.body).toHaveProperty('order');
    expect(response.body.order.id).toBe(1);
  });

  test('should create new order', async () => {
    const newOrder = {
      userId: 1,
      product: 'Test Product',
      amount: 99.99
    };

    const response = await request(app)
      .post('/api/orders')
      .send(newOrder)
      .expect(201);

    expect(response.body).toHaveProperty('order');
    expect(response.body.order.product).toBe(newOrder.product);
  });

  test('should handle high value orders', async () => {
    const highValueOrder = {
      userId: 1,
      product: 'Expensive Item',
      amount: 1500.00
    };

    const response = await request(app)
      .post('/api/orders')
      .send(highValueOrder)
      .expect(201);

    expect(response.body.order.status).toBe('requires_approval');
  });

  // FLAKY TEST - database simulation
  test('flaky test - simulated database issues', async () => {
    // This test simulates intermittent database connectivity issues
    const hasDbIssue = Math.random() < 0.25; // 25% chance of failure
    
    if (hasDbIssue) {
      // Simulate database timeout
      await new Promise(resolve => setTimeout(resolve, 100));
      throw new Error('Database connection timeout - flaky test');
    }

    const response = await request(app)
      .get('/api/orders')
      .expect(200);

    expect(response.body.orders).toBeDefined();
  });

  // FLAKY TEST - race condition simulation
  test('flaky test - race condition in order creation', async () => {
    const promises = [];
    
    // Create multiple orders simultaneously to simulate race condition
    for (let i = 0; i < 3; i++) {
      promises.push(
        request(app)
          .post('/api/orders')
          .send({
            userId: 1,
            product: `Race Product ${i}`,
            amount: 50.00
          })
      );
    }

    const responses = await Promise.all(promises);
    
    // Flaky assertion - sometimes the order IDs might not be sequential due to race conditions
    const orderIds = responses.map(r => r.body.order.id);
    const isSequential = orderIds.every((id, index) => 
      index === 0 || id === orderIds[index - 1] + 1
    );

    if (!isSequential && Math.random() < 0.4) {
      throw new Error('Race condition detected in order ID assignment');
    }

    responses.forEach(response => {
      expect(response.status).toBe(201);
    });
  });

  test('should trigger intentional error for order 666', async () => {
    const response = await request(app)
      .get('/api/orders/666')
      .expect(500);

    expect(response.body).toHaveProperty('error');
    expect(response.body.message).toContain('intentional error');
  });

  test('should simulate database error for order 500', async () => {
    const response = await request(app)
      .get('/api/orders/500')
      .expect(500);

    expect(response.body).toHaveProperty('error');
  });

  test('should get orders by user', async () => {
    const response = await request(app)
      .get('/api/orders/user/1')
      .expect(200);

    expect(response.body).toHaveProperty('orders');
    expect(response.body).toHaveProperty('cache_hit');
    expect(response.body.user_id).toBe(1);
  });

  // FLAKY TEST - cache behavior
  test('flaky test - cache hit rate expectations', async () => {
    const responses = [];
    
    // Make multiple requests to test cache behavior
    for (let i = 0; i < 5; i++) {
      const response = await request(app)
        .get('/api/orders/user/1');
      responses.push(response.body);
    }

    const cacheHits = responses.filter(r => r.cache_hit).length;
    const cacheHitRate = cacheHits / responses.length;

    // Flaky assertion - expects high cache hit rate but it's random
    if (cacheHitRate < 0.6 && Math.random() < 0.3) {
      throw new Error(`Cache hit rate too low: ${cacheHitRate * 100}%`);
    }

    expect(responses.length).toBe(5);
  });
});
