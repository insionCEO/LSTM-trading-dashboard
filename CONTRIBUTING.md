# Contributing to AI Trading System

Thank you for your interest in contributing to the AI Trading System! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## 📝 Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose

### Testing
- Write tests for new features
- Ensure all tests pass before submitting
- Run the test suite:
  ```bash
  python -m pytest tests/
  ```

### Documentation
- Update README.md for new features
- Add inline comments for complex logic
- Update docstrings when changing function signatures

## 🔧 Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit them:
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** on GitHub

## 🐛 Reporting Issues

When reporting issues, please include:
- **Description** of the problem
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Error messages** or logs

## 💡 Feature Requests

For feature requests:
- **Describe the feature** in detail
- **Explain the use case** and benefits
- **Consider implementation complexity**
- **Check if it aligns** with project goals

## 📋 Pull Request Checklist

Before submitting a PR, ensure:
- [ ] Code follows style guidelines
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] No sensitive data is included
- [ ] Changes are focused and minimal

## 🤝 Code Review

- Be respectful and constructive
- Focus on the code, not the person
- Provide specific, actionable feedback
- Be patient with maintainers

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🆘 Getting Help

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check the README and inline docs first

Thank you for contributing! 🎉 