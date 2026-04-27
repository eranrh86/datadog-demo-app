const express = require('express');
const logger = require('../utils/logger');
const { asyncHandler } = require('../middleware/errorHandler');
const router = express.Router();

// Mock orders database
let orders = [
  { id: 1, userId: 1, product: 'Laptop', amount: 999.99, status: 'completed' },
  { id: 2, userId: 2, product: 'Mouse', amount: 29.99, status: 'pending' },
  { id: 3, userId: 1, product: 'Keyboard', amount: 79.99, status: 'shipped' }
];

// Get all orders with performance monitoring
router.get('/', asyncHandler(async (req, res) => {
  const startTime = Date.now();
  
  logger.info('Fetching all orders', {
    operation: 'get_orders',
    order_count: orders.length
  });

  // Simulate slow database query for performance monitoring
  const delay = Math.random() * 500; // 0-500ms delay
  await new Promise(resolve => setTimeout(resolve, delay));

  const duration = Date.now() - startTime;
  
  logger.histogram('orders.fetch_duration', duration);
  logger.gauge('orders.total_count', orders.length);
  logger.increment('orders.fetch_requests', 1);

  // Log performance warning if slow
  if (duration > 200) {
    logger.warn('Slow order fetch detected', {
      operation: 'get_orders',
      duration: duration,
      performance_issue: true
    });
  }

  res.json({
    orders: orders,
    total: orders.length,
    fetch_duration: duration,
    timestamp: new Date().toISOString()
  });
}));

// Get order by ID with error scenarios
router.get('/:id', asyncHandler(async (req, res) => {
  const orderId = parseInt(req.params.id);
  
  logger.info('Fetching order by ID', {
    operation: 'get_order_by_id',
    order_id: orderId
  });

  // Intentional error for Exception Replay demo
  if (orderId === 666) {
    logger.error('Intentional error triggered for order 666', {
      operation: 'get_order_by_id',
      order_id: orderId,
      error_type: 'intentional_demo_error'
    });
    
    throw new Error('Order 666 triggers intentional error for demo purposes');
  }

  // Simulate database connection issues
  if (orderId === 500) {
    const dbError = new Error('Database connection timeout');
    dbError.code = 'ECONNRESET';
    dbError.statusCode = 500;
    
    logger.error('Database connection error', {
      operation: 'get_order_by_id',
      order_id: orderId,
      error_code: dbError.code,
      error_type: 'database_error'
    });
    
    throw dbError;
  }

  const order = orders.find(o => o.id === orderId);
  
  if (!order) {
    logger.warn('Order not found', {
      operation: 'get_order_by_id',
      order_id: orderId,
      error_type: 'not_found'
    });
    
    return res.status(404).json({
      error: 'Order not found',
      order_id: orderId
    });
  }

  logger.info('Order found successfully', {
    operation: 'get_order_by_id',
    order_id: orderId,
    order_status: order.status,
    order_amount: order.amount
  });

  res.json({ order });
}));

// Create new order with business logic
router.post('/', asyncHandler(async (req, res) => {
  const { userId, product, amount } = req.body;
  
  logger.info('Creating new order', {
    operation: 'create_order',
    user_id: userId,
    product: product,
    amount: amount
  });

  // Validation
  if (!userId || !product || !amount) {
    logger.error('Order creation failed - missing required fields', {
      operation: 'create_order',
      validation_error: 'missing_fields',
      provided_fields: Object.keys(req.body)
    });
    
    return res.status(400).json({
      error: 'UserId, product, and amount are required'
    });
  }

  // Business logic with potential issues
  let orderStatus = 'pending';
  
  // VULNERABILITY: Potential race condition (for Code Insights demo)
  if (amount > 1000) {
    // Simulate approval process delay
    await new Promise(resolve => setTimeout(resolve, 100));
    orderStatus = 'requires_approval';
    
    logger.warn('High value order requires approval', {
      operation: 'create_order',
      amount: amount,
      requires_approval: true,
      security_flag: true
    });
  }

  const newOrder = {
    id: orders.length + 1,
    userId: parseInt(userId),
    product,
    amount: parseFloat(amount),
    status: orderStatus,
    createdAt: new Date().toISOString()
  };

  orders.push(newOrder);

  logger.info('Order created successfully', {
    operation: 'create_order',
    order_id: newOrder.id,
    user_id: newOrder.userId,
    amount: newOrder.amount,
    status: newOrder.status
  });

  // Metrics
  logger.increment('orders.created_count', 1);
  logger.gauge('orders.total_count', orders.length);
  logger.histogram('orders.amount_distribution', newOrder.amount);

  res.status(201).json({ order: newOrder });
}));

// Update order status
router.patch('/:id/status', asyncHandler(async (req, res) => {
  const orderId = parseInt(req.params.id);
  const { status } = req.body;
  
  logger.info('Updating order status', {
    operation: 'update_order_status',
    order_id: orderId,
    new_status: status
  });

  const order = orders.find(o => o.id === orderId);
  
  if (!order) {
    logger.warn('Order status update failed - order not found', {
      operation: 'update_order_status',
      order_id: orderId
    });
    
    return res.status(404).json({
      error: 'Order not found'
    });
  }

  const oldStatus = order.status;
  order.status = status;
  order.updatedAt = new Date().toISOString();

  logger.info('Order status updated successfully', {
    operation: 'update_order_status',
    order_id: orderId,
    old_status: oldStatus,
    new_status: status
  });

  logger.increment('orders.status_updates', 1, {
    from_status: oldStatus,
    to_status: status
  });

  res.json({ order });
}));

// Get orders by user with caching simulation
router.get('/user/:userId', asyncHandler(async (req, res) => {
  const userId = parseInt(req.params.userId);
  
  logger.info('Fetching orders by user', {
    operation: 'get_orders_by_user',
    user_id: userId
  });

  // Simulate cache miss/hit
  const cacheHit = Math.random() > 0.3; // 70% cache hit rate
  
  if (cacheHit) {
    logger.info('Cache hit for user orders', {
      operation: 'get_orders_by_user',
      user_id: userId,
      cache_status: 'hit'
    });
  } else {
    logger.info('Cache miss for user orders', {
      operation: 'get_orders_by_user',
      user_id: userId,
      cache_status: 'miss'
    });
    
    // Simulate database query delay on cache miss
    await new Promise(resolve => setTimeout(resolve, 150));
  }

  const userOrders = orders.filter(o => o.userId === userId);

  logger.info('User orders fetched successfully', {
    operation: 'get_orders_by_user',
    user_id: userId,
    order_count: userOrders.length,
    cache_status: cacheHit ? 'hit' : 'miss'
  });

  logger.gauge('orders.user_order_count', userOrders.length, {
    user_id: userId.toString()
  });

  res.json({
    orders: userOrders,
    user_id: userId,
    total: userOrders.length,
    cache_hit: cacheHit
  });
}));

module.exports = router;
