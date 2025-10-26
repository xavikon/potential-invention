# Contributing to CMIS Module Emulator

First off, thank you for considering contributing to the CMIS Module Emulator! It's people like you that make this tool better for everyone.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps which reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps**
* **Explain which behavior you expected to see instead and why**
* **Include any relevant logs or screenshots**

### Suggesting Enhancements

If you have a suggestion for the project, we'd love to hear about it! Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a step-by-step description of the suggested enhancement**
* **Provide specific examples to demonstrate the steps**
* **Describe the current behavior and explain what behavior you expected to see instead**
* **Explain why this enhancement would be useful**

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Follow the Python style guide (PEP 8)
* Include appropriate test coverage
* Document new code based on the Documentation Styleguide
* End all files with a newline

## Development Process

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the style guidelines
6. Issue that pull request!

### Local Development

Here's how to set up the CMIS Module Emulator for local development:

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone git@github.com:your-username/cmis.git
   ```
3. Create a branch for local development:
   ```bash
   git checkout -b name-of-your-bugfix-or-feature
   ```
4. Set up your environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
5. When you're done making changes:
   ```bash
   pytest
   ```
6. Commit your changes:
   ```bash
   git add .
   git commit -m "Your detailed description of your changes"
   ```
7. Push your branch to GitHub:
   ```bash
   git push origin name-of-your-bugfix-or-feature
   ```
8. Submit a pull request through GitHub

### Testing

We use pytest for our test suite. To run tests:

```bash
python -m pytest tests/
```

For coverage report:
```bash
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### Documentation

We use Doxygen for documentation. Please document your code using Doxygen-style comments:

```python
"""!
@brief Brief description
@details Detailed description
@param param_name Parameter description
@return Return value description
"""
```

## Style Guide

* Follow PEP 8 for Python code
* Use descriptive variable names
* Comment your code
* Keep functions focused and small
* Write docstrings for all public methods and functions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue with your question or contact the maintainers directly.

Thank you for contributing! 🎉