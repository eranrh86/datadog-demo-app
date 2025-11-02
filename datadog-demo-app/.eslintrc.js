module.exports = {
  env: {
    node: true,
    es2021: true,
    jest: true
  },
  extends: [
    'eslint:recommended'
  ],
  plugins: [
    'security'
  ],
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module'
  },
  rules: {
    // Security rules for Code Insights demo
    'security/detect-sql-injection': 'error',
    'security/detect-eval-with-expression': 'error',
    'security/detect-non-literal-regexp': 'warn',
    'security/detect-unsafe-regex': 'error',
    'security/detect-buffer-noassert': 'error',
    'security/detect-child-process': 'warn',
    'security/detect-disable-mustache-escape': 'error',
    'security/detect-no-csrf-before-method-override': 'error',
    'security/detect-object-injection': 'error',
    'security/detect-possible-timing-attacks': 'warn',
    'security/detect-pseudoRandomBytes': 'error',
    
    // Code quality rules
    'no-unused-vars': 'warn',
    'no-console': 'warn',
    'no-debugger': 'error',
    'no-alert': 'error',
    'no-eval': 'error',
    'no-implied-eval': 'error',
    'no-new-func': 'error',
    'no-script-url': 'error',
    'no-proto': 'error',
    'no-iterator': 'error',
    'no-with': 'error',
    
    // Best practices
    'eqeqeq': 'error',
    'curly': 'error',
    'dot-notation': 'warn',
    'no-multi-spaces': 'warn',
    'no-trailing-spaces': 'warn',
    'semi': ['error', 'always'],
    'quotes': ['warn', 'single'],
    'indent': ['warn', 2],
    
    // Potential problems
    'no-unreachable': 'error',
    'no-constant-condition': 'warn',
    'no-duplicate-case': 'error',
    'no-empty': 'warn',
    'no-extra-boolean-cast': 'warn',
    'no-extra-semi': 'warn',
    'no-func-assign': 'error',
    'no-inner-declarations': 'error',
    'no-invalid-regexp': 'error',
    'no-irregular-whitespace': 'error',
    'no-obj-calls': 'error',
    'no-sparse-arrays': 'error',
    'no-unexpected-multiline': 'error',
    'use-isnan': 'error',
    'valid-typeof': 'error'
  },
  overrides: [
    {
      files: ['tests/**/*.js', '**/*.test.js'],
      rules: {
        'no-unused-expressions': 'off'
      }
    }
  ]
};
