# Contributing

Thank you for your interest in contributing to QUADS Client!

## Getting Started

1. Fork the repository (uncheck _only main branch_)
2. Checkout `development` branch

```bash
git checkout development
git checkout -b mybranch
```

3. Make your changes following DRY principles
4. Format code with black (line-length 119)
5. Test thoroughly and push your local changes.

```bash
git push -u origin mybranch
```

6. Submit a pull request to the `development` branch

## Code Standards

- Follow DRY (Don't Repeat Yourself) principles
- Use black for code formatting with line-length 119
- Write tests for new functionality
- Maintain or improve test coverage (currently 73%+)
- Keep code simple and maintainable

## Testing

* You can use the following command to run quads-client directly from the repository:

```bash
PYTHONPATH=src python3 -c "from quads_client.shell import QuadsClientShell; shell = QuadsClientShell(); shell.cmdloop()"
```

Before submitting a pull request, ensure:

```bash
# Run tests with coverage
python -m pytest --cov=src/quads_client --cov-report=term-missing -v

# Check code style
python -m flake8 src/ tests/ --count --max-line-length=119 --statistics
```

## Questions?

- Open an issue: https://github.com/quadsproject/quads-client/issues
- See project documentation: https://quads.dev
