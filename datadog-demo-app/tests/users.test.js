const request = require('supertest');
const app = require('../src/app');

describe('Users API', () => {
  test('should get all users', async () => {
    const response = await request(app)
      .get('/api/users')
      .expect(200);

    expect(response.body).toHaveProperty('users');
    expect(Array.isArray(response.body.users)).toBe(true);
    expect(response.body.total).toBeGreaterThan(0);
  });

  test('should get user by ID', async () => {
    const response = await request(app)
      .get('/api/users/1')
      .expect(200);

    expect(response.body).toHaveProperty('user');
    expect(response.body.user.id).toBe(1);
  });

  test('should return 404 for non-existent user', async () => {
    const response = await request(app)
      .get('/api/users/9999')
      .expect(404);

    expect(response.body).toHaveProperty('error');
  });

  test('should create new user', async () => {
    const newUser = {
      name: 'Test User',
      email: 'test@example.com',
      role: 'user'
    };

    const response = await request(app)
      .post('/api/users')
      .send(newUser)
      .expect(201);

    expect(response.body).toHaveProperty('user');
    expect(response.body.user.name).toBe(newUser.name);
    expect(response.body.user.email).toBe(newUser.email);
  });

  // FLAKY TEST for demo purposes
  test('flaky test - sometimes fails randomly', async () => {
    // This test will fail randomly ~30% of the time
    const shouldFail = Math.random() < 0.3;
    
    if (shouldFail) {
      // Simulate a flaky test failure
      throw new Error('Flaky test failure - network timeout simulation');
    }

    const response = await request(app)
      .get('/api/users')
      .expect(200);

    expect(response.body.users).toBeDefined();
  });

  // Another FLAKY TEST with timing issues
  test('flaky test - timing dependent', async () => {
    const startTime = Date.now();
    
    const response = await request(app)
      .get('/api/users/1')
      .expect(200);

    const duration = Date.now() - startTime;
    
    // This test fails if the response takes longer than 50ms (flaky timing)
    if (duration > 50) {
      throw new Error(`Test failed due to slow response: ${duration}ms`);
    }

    expect(response.body.user).toBeDefined();
  });

  test('should handle user creation validation', async () => {
    const invalidUser = {
      name: 'Test User'
      // Missing email
    };

    const response = await request(app)
      .post('/api/users')
      .send(invalidUser)
      .expect(400);

    expect(response.body).toHaveProperty('error');
  });

  test('should trigger runtime error for user 999', async () => {
    // This test expects a 500 error due to intentional runtime error
    const response = await request(app)
      .get('/api/users/999')
      .expect(500);

    expect(response.body).toHaveProperty('error');
  });
});
