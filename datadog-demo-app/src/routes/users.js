const express = require('express');
const logger = require('../utils/logger');
const { asyncHandler } = require('../middleware/errorHandler');
const router = express.Router();

// Mock user database
let users = [
  { id: 1, name: 'John Doe', email: 'john@example.com', role: 'admin' },
  { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'user' },
  { id: 3, name: 'Bob Johnson', email: 'bob@example.com', role: 'user' }
];

// Get all users with log annotations
router.get('/', asyncHandler(async (req, res) => {
  logger.info('Fetching all users', {
    operation: 'get_users',
    user_count: users.length,
    request_source: req.ip
  });

  // Simulate database query delay
  await new Promise(resolve => setTimeout(resolve, Math.random() * 100));

  logger.gauge('users.total_count', users.length);
  logger.increment('users.fetch_requests', 1);

  res.json({
    users: users,
    total: users.length,
    timestamp: new Date().toISOString()
  });
}));

// Get user by ID with potential runtime error
router.get('/:id', asyncHandler(async (req, res) => {
  const userId = parseInt(req.params.id);
  
  logger.info('Fetching user by ID', {
    operation: 'get_user_by_id',
    user_id: userId,
    request_source: req.ip
  });

  // Intentional bug for Code Insights - potential runtime error
  if (userId === 999) {
    // This will cause a runtime error for demo purposes
    const undefinedUser = null;
    return res.json({ user: undefinedUser.profile.details });
  }

  const user = users.find(u => u.id === userId);
  
  if (!user) {
    logger.warn('User not found', {
      operation: 'get_user_by_id',
      user_id: userId,
      error_type: 'not_found'
    });
    
    return res.status(404).json({
      error: 'User not found',
      user_id: userId
    });
  }

  logger.info('User found successfully', {
    operation: 'get_user_by_id',
    user_id: userId,
    user_name: user.name
  });

  res.json({ user });
}));

// Create new user with validation
router.post('/', asyncHandler(async (req, res) => {
  const { name, email, role } = req.body;
  
  logger.info('Creating new user', {
    operation: 'create_user',
    user_name: name,
    user_email: email,
    user_role: role
  });

  // Validation (intentionally weak for security demo)
  if (!name || !email) {
    logger.error('User creation failed - missing required fields', {
      operation: 'create_user',
      validation_error: 'missing_fields',
      provided_fields: Object.keys(req.body)
    });
    
    return res.status(400).json({
      error: 'Name and email are required'
    });
  }

  // VULNERABILITY: No email validation (for Code Insights demo)
  const newUser = {
    id: users.length + 1,
    name,
    email, // No validation - potential security issue
    role: role || 'user'
  };

  users.push(newUser);

  logger.info('User created successfully', {
    operation: 'create_user',
    user_id: newUser.id,
    user_name: newUser.name
  });

  logger.increment('users.created_count', 1);
  logger.gauge('users.total_count', users.length);

  res.status(201).json({ user: newUser });
}));

// Update user with potential issues
router.put('/:id', asyncHandler(async (req, res) => {
  const userId = parseInt(req.params.id);
  const updates = req.body;
  
  logger.info('Updating user', {
    operation: 'update_user',
    user_id: userId,
    update_fields: Object.keys(updates)
  });

  const userIndex = users.findIndex(u => u.id === userId);
  
  if (userIndex === -1) {
    logger.warn('User update failed - user not found', {
      operation: 'update_user',
      user_id: userId
    });
    
    return res.status(404).json({
      error: 'User not found'
    });
  }

  // VULNERABILITY: No input sanitization (for Code Insights demo)
  Object.assign(users[userIndex], updates);

  logger.info('User updated successfully', {
    operation: 'update_user',
    user_id: userId,
    updated_user: users[userIndex]
  });

  logger.increment('users.updated_count', 1);

  res.json({ user: users[userIndex] });
}));

// Delete user
router.delete('/:id', asyncHandler(async (req, res) => {
  const userId = parseInt(req.params.id);
  
  logger.info('Deleting user', {
    operation: 'delete_user',
    user_id: userId
  });

  const userIndex = users.findIndex(u => u.id === userId);
  
  if (userIndex === -1) {
    logger.warn('User deletion failed - user not found', {
      operation: 'delete_user',
      user_id: userId
    });
    
    return res.status(404).json({
      error: 'User not found'
    });
  }

  const deletedUser = users.splice(userIndex, 1)[0];

  logger.info('User deleted successfully', {
    operation: 'delete_user',
    user_id: userId,
    deleted_user_name: deletedUser.name
  });

  logger.increment('users.deleted_count', 1);
  logger.gauge('users.total_count', users.length);

  res.json({ 
    message: 'User deleted successfully',
    deleted_user: deletedUser
  });
}));

module.exports = router;
