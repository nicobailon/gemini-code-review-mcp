# Contributing to gemini-code-review-mcp

Thank you for your interest in contributing to gemini-code-review-mcp! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Git Hooks](#git-hooks)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/nicobailon/gemini-code-review-mcp.git
   cd gemini-code-review-mcp
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install git hooks** (Recommended)
   ```bash
   ./scripts/install-hooks.sh
   ```

## Git Hooks

This project uses git hooks to maintain code quality and enforce development workflows. The hooks help prevent common mistakes and ensure all code meets our quality standards before it reaches the main branch.

### Available Hooks

1. **pre-commit**: Runs when committing to master/main branches
   - Executes the full test suite to ensure no broken code is committed
   - Performs syntax checks on Python files for feature branches
   
2. **pre-push**: Prevents direct pushes to master/main branches
   - Enforces the pull request workflow
   - Provides helpful guidance on creating feature branches

### Installing Git Hooks

```bash
# Install hooks (recommended for all contributors)
./scripts/install-hooks.sh

# Uninstall hooks if needed
./scripts/uninstall-hooks.sh
```

### Bypassing Hooks (Emergency Use Only)

In rare cases where you need to bypass the hooks:

```bash
# Bypass pre-commit hook
git commit --no-verify

# Bypass pre-push hook
git push --no-verify
```

⚠️ **Please use these flags responsibly and only when absolutely necessary!**

## Development Workflow

We follow a feature branch workflow to maintain code quality:

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```
   
   We follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/modifications
   - `chore:` for maintenance tasks

4. **Push to your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Go to GitHub and create a PR from your branch to master
   - Fill out the PR template with details about your changes
   - Request review from maintainers

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_specific.py

# Run with coverage
python -m pytest tests/ --cov=src
```

### Writing Tests

- Place tests in the `tests/` directory
- Follow the existing test structure and naming conventions
- Aim for high test coverage, especially for new features
- Use mocks for external dependencies (Gemini API, file system, etc.)

## Code Style

### Python Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **pyright** for type checking

Run these tools before committing:

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
pyright src/
```

### Type Annotations

- Use type hints for all function signatures
- Follow strict typing guidelines (no `Any` types unless absolutely necessary)
- Ensure pyright passes with no errors

## Submitting Changes

### Pull Request Guidelines

1. **PR Title**: Use a clear, descriptive title following conventional commits
2. **Description**: Explain what changes you made and why
3. **Tests**: Ensure all tests pass and add new tests for new features
4. **Documentation**: Update relevant documentation
5. **Small PRs**: Keep PRs focused on a single feature or fix

### Code Review Process

1. All PRs require at least one review from a maintainer
2. Address review feedback promptly
3. Keep discussions professional and constructive
4. Once approved, the PR will be merged by a maintainer

### After Your PR is Merged

- Delete your feature branch
- Pull the latest master to your local repository
- Celebrate your contribution! 🎉

## Questions or Need Help?

- Open an issue for bugs or feature requests
- Start a discussion for general questions
- Tag maintainers for urgent matters

Thank you for contributing to gemini-code-review-mcp!