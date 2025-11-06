# Contributing to MCP Multi-Context Memory System

Copyright (c) 2024 VoiceLessQ
Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024

Thank you for your interest in contributing to the MCP Multi-Context Memory System!

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Copyright & Licensing](#copyright--licensing)
- [Development Guidelines](#development-guidelines)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

By participating in this project, you agree to:

1. Respect the project's copyright and licensing terms
2. Provide constructive and respectful feedback
3. Maintain the integrity of the codebase
4. Not remove or modify copyright notices
5. Follow the MIT License terms

---

## Getting Started

### Prerequisites

- Python 3.8+ (3.11 recommended)
- Git
- Docker & Docker Compose (optional, for containerized development)

### Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/multi-context-memory.git
   cd multi-context-memory
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/VoiceLessQ/multi-context-memory.git
   ```

4. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## How to Contribute

### Types of Contributions

We welcome the following contributions:

- 🐛 **Bug Reports**: Found a bug? Open an issue with details
- 💡 **Feature Requests**: Have an idea? Describe it in an issue
- 📝 **Documentation**: Improve docs, add examples, fix typos
- 🔧 **Bug Fixes**: Submit PRs to fix reported issues
- ✨ **Features**: Implement new features (discuss first in issues)
- 🧪 **Tests**: Add or improve test coverage
- 🎨 **Code Quality**: Refactoring, optimization, cleanup

### Before You Start

1. **Search existing issues** to avoid duplicates
2. **Open an issue** to discuss major changes before implementing
3. **Check the roadmap** in README.md to align with project direction

---

## Copyright & Licensing

### Important Copyright Requirements

**All contributions must comply with these requirements:**

1. ✅ **Retain all existing copyright notices** in files you modify
2. ✅ **Do not remove the project fingerprint** (7a8f9b3c-mcpmem-voicelessq-2024)
3. ✅ **Do not remove or modify the LICENSE file**
4. ✅ **Do not remove or modify the NOTICE file**
5. ✅ **New files must include the standard copyright header** (see below)

### Standard Copyright Header for New Files

Add this header to all new Python files:

```python
"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

This file is part of the MCP Multi-Context Memory System.
Licensed under the MIT License. See LICENSE file in the project root.

Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
Original Author: VoiceLessQ
"""
```

### License Terms

By contributing, you agree that:

1. Your contributions will be licensed under the **MIT License**
2. You have the right to submit the contribution
3. You grant the project maintainers the right to use, modify, and distribute your contributions
4. You understand this is an open-source project
5. You will not submit code that violates others' copyrights or licenses

### Contributor License Agreement (Implicit)

By submitting a pull request, you implicitly agree to the following:

- You certify that your contribution is your original work OR you have the right to submit it
- You understand your contribution will be publicly available under the MIT License
- You grant VoiceLessQ and the project a perpetual, worldwide license to use, modify, and distribute your contribution
- You will not seek to revoke these rights in the future

---

## Development Guidelines

### Code Style

- Follow **PEP 8** for Python code
- Use **type hints** where applicable
- Write **docstrings** for all public functions and classes
- Keep functions focused and under 50 lines when possible
- Use meaningful variable names

### Code Quality

- ✅ Run tests before submitting: `pytest tests/`
- ✅ Check code style: `flake8 src/`
- ✅ Type checking: `mypy src/`
- ✅ Security scan: `pip-audit -r requirements.txt`

### Testing

- Add tests for new features
- Ensure existing tests pass
- Aim for >70% code coverage
- Include both unit and integration tests

### Documentation

- Update README.md if adding features
- Add docstrings to new functions/classes
- Update relevant docs in `/docs` directory
- Include examples for new features

---

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Write clean, well-documented code
- Add copyright headers to new files
- Include tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
pytest tests/

# Check code style
flake8 src/

# Verify copyright headers
python add_copyright_headers.py
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: Add vector search optimization

- Implement caching for embedding queries
- Add batch processing for large datasets
- Update documentation with usage examples
"
```

**Commit message format:**

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `security:` - Security fixes

### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 6. Open a Pull Request

1. Go to the [original repository](https://github.com/VoiceLessQ/multi-context-memory)
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template:
   - **Title**: Clear, concise description
   - **Description**: What changed and why
   - **Related Issues**: Link to related issues
   - **Testing**: How you tested the changes
   - **Checklist**: Complete the PR checklist

### 7. Code Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Once approved, your PR will be merged

---

## Project Structure

```
multi-context-memory/
├── src/                    # Source code
│   ├── api/                # FastAPI REST API
│   ├── mcp/                # MCP server implementation
│   ├── database/           # Database models & repositories
│   ├── services/           # Business logic services
│   └── utils/              # Utility functions
├── tests/                  # Test suite
├── docs/                   # Documentation
├── .github/                # GitHub Actions workflows
├── LICENSE                 # MIT License (DO NOT MODIFY)
├── NOTICE                  # Attribution notice (DO NOT MODIFY)
├── SECURITY.md             # Security policy
└── requirements.txt        # Python dependencies
```

---

## Questions or Need Help?

- 📧 **Issues**: Open an issue on GitHub
- 💬 **Discussions**: Use GitHub Discussions for questions
- 📖 **Docs**: Check the `/docs` directory

---

## Recognition

Contributors will be recognized in:
- The project's contributor list (automatically via GitHub)
- Release notes for significant contributions
- Special mentions in documentation for major features

---

## Final Notes

### What We're Looking For

✅ Quality over quantity
✅ Clear, well-documented code
✅ Thoughtful, tested changes
✅ Respect for the project's goals and architecture

### What We Don't Accept

❌ Removing copyright notices
❌ Changing licensing terms
❌ Low-quality or untested code
❌ Breaking changes without discussion
❌ Violations of the Code of Conduct

---

**Thank you for contributing to the MCP Multi-Context Memory System!** 🚀

*This project is maintained by VoiceLessQ and licensed under the MIT License.*
*Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024*
