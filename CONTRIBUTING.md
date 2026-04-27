# Contributing to Datadog Demo App

First off, thank you for considering contributing to the Datadog Demo App! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to providing a welcoming and inclusive environment. Please be respectful and constructive in all interactions.

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Environment details** (Node.js version, OS, etc.)
- **Screenshots or logs** if applicable

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why is this enhancement useful?
- **Proposed solution** or implementation approach
- **Alternative solutions** you've considered

### 🔧 Adding Demo Scenarios

We're always looking for new demo scenarios! Consider adding:

- New error scenarios for Exception Replay
- Additional security vulnerabilities for Code Insights
- Performance issues for APM demonstrations
- Flaky test examples
- Integration examples with other Datadog features

### 📝 Improving Documentation

Documentation improvements are always welcome:

- Fix typos or clarify existing docs
- Add missing documentation
- Create tutorials or guides
- Improve code comments

## Development Setup

### Prerequisites

- Node.js 16 or higher
- npm or yarn
- Git
- Datadog account (for testing)

### Setup Steps

1. **Fork the repository**

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/datadog-demo-app.git
   cd datadog-demo-app
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/eranrh86/datadog-demo-app.git
   ```

4. **Install dependencies**
   ```bash
   npm install
   ```

5. **Set up environment variables**
   ```bash
   export DD_API_KEY=your_test_api_key
   export DD_SERVICE=datadog-demo-app-dev
   export DD_ENV=development
   ```

6. **Run the application**
   ```bash
   npm start
   ```

7. **Run tests**
   ```bash
   npm test
   ```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow the existing code style
   - Add tests if applicable
   - Update documentation as needed

3. **Test your changes**
   ```bash
   npm test
   npm run lint
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new demo scenario for X"
   ```

   Use conventional commit messages:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting, etc.)
   - `refactor:` - Code refactoring
   - `test:` - Adding or updating tests
   - `chore:` - Maintenance tasks

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template with details

### PR Requirements

- ✅ All tests pass
- ✅ No linting errors
- ✅ Documentation updated (if needed)
- ✅ Clear description of changes
- ✅ Linked to related issues (if any)

## Style Guidelines

### JavaScript Style

- Use **ES6+** syntax
- Use **async/await** over callbacks
- Use **const** and **let**, avoid **var**
- Use **meaningful variable names**
- Add **comments** for complex logic
- Follow **ESLint** configuration

### Code Example

```javascript
// Good
const fetchUserData = async (userId) => {
  try {
    const user = await User.findById(userId);
    if (!user) {
      throw new Error('User not found');
    }
    return user;
  } catch (error) {
    logger.error('Failed to fetch user', { userId, error });
    throw error;
  }
};

// Avoid
function getUserData(userId, callback) {
  User.findById(userId, function(err, user) {
    if (err) return callback(err);
    callback(null, user);
  });
}
```

### Commit Message Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Examples:**

```
feat(orders): add new error scenario for database timeout

Added a new endpoint that simulates database connection timeout
to demonstrate Exception Replay capabilities.

Closes #123
```

```
docs(readme): update installation instructions

- Added Docker installation steps
- Clarified environment variable requirements
- Fixed broken links
```

### Testing Guidelines

- Write tests for new features
- Ensure existing tests still pass
- Use descriptive test names
- Test both success and error cases

```javascript
describe('User API', () => {
  it('should return user when valid ID is provided', async () => {
    // Test implementation
  });

  it('should throw error when user not found', async () => {
    // Test implementation
  });
});
```

## Questions?

Feel free to:
- Open an issue for discussion
- Reach out to the maintainers
- Check existing documentation

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes (for significant contributions)
- Project documentation

---

Thank you for contributing! 🙏

**Happy coding!** 🚀

