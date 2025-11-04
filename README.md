# AI Tester Framework v3.0

> A well-structured, testable framework for AI-powered test case generation with multi-agent collaboration

## 🎯 Overview

This is a complete refactoring of the AI Tester tool from a monolithic 7,327-line script into a modern, maintainable Python framework with:

- **✅ Test-Driven Development** - Every component has comprehensive unit tests
- **🏗️ Clean Architecture** - Separated concerns with clear module boundaries  
- **🤖 Multi-Agent System** - Strategic planning, evaluation, and validation agents
- **📦 Modular Design** - Easy to extend, test, and maintain
- **🔧 Modern Python** - Type hints, dataclasses, and best practices

## 📁 Project Structure

```
ai-tester/
├── src/ai_tester/          # Main application code
│   ├── core/               # Core business logic
│   │   ├── models.py       # Data models (TestCase, etc.)
│   │   ├── jira_client.py  # Jira API integration
│   │   └── llm_client.py   # OpenAI API integration
│   ├── agents/             # Multi-agent system
│   ├── orchestrators/      # Agent orchestration
│   └── utils/              # Utilities
│
├── tests/                  # Comprehensive test suite
│   ├── core/               # Tests for core modules
│   ├── agents/             # Tests for agents
│   └── conftest.py         # Pytest fixtures
│
├── legacy/                 # Original v2 code (for reference)
└── docs/                   # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager
- OpenAI API key
- Jira API credentials

### Installation

1. **Clone or extract the project**

2. **Run the automated setup** (recommended):
   ```bash
   python setup_and_test.py
   ```
   
   This will:
   - Install all dependencies
   - Install the package in editable mode
   - Run the test suite
   - Verify everything is working

3. **Or install manually**:
   ```bash
   # Install production dependencies
   pip install -r requirements.txt
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Install the package in editable mode
   pip install -e .
   
   # Run tests
   pytest tests/ -v
   ```

### Verify Installation

```bash
# Run all unit tests (fast)
pytest tests/ -m "not integration" -v

# Run tests with coverage
pytest tests/ --cov=src/ai_tester --cov-report=html

# View coverage report
# open htmlcov/index.html
```

If all tests pass ✅, you're ready to start developing!

## 📚 Documentation

- **[FRAMEWORK_MIGRATION_PLAN.md](FRAMEWORK_MIGRATION_PLAN.md)** - Complete migration strategy and implementation plan
- **[START_HERE.md](START_HERE.md)** - Overview of the v2 code and multi-agent vision
- **[MULTI_AGENT_ACTION_PLAN.md](MULTI_AGENT_ACTION_PLAN.md)** - 12-week implementation roadmap

## 🧪 Testing

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── core/
│   ├── test_models.py       # Data model tests (55+ tests)
│   ├── test_jira_client.py  # Jira integration tests
│   └── test_llm_client.py   # LLM integration tests
└── agents/
    ├── test_base_agent.py
    └── test_strategic_planner.py
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/core/test_models.py -v

# Run tests matching pattern
pytest tests/ -k "test_create" -v

# Run with coverage
pytest tests/ --cov=src/ai_tester --cov-report=term-missing

# Run only unit tests (fast)
pytest tests/ -m "unit"

# Run only integration tests
pytest tests/ -m "integration"

# Run with verbose output
pytest tests/ -vv

# Stop on first failure
pytest tests/ -x
```

### Test Markers

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests (may use real APIs)
- `@pytest.mark.slow` - Tests that take >1 second
- `@pytest.mark.requires_api_key` - Tests requiring API credentials

### Writing Tests

Follow the TDD approach demonstrated in the existing tests:

1. **Write the test first**
2. **Make it pass**
3. **Refactor**

Example:
```python
# tests/core/test_my_feature.py
def test_my_new_feature():
    """Test description"""
    result = my_function(input_data)
    assert result == expected_output
```

## 🏗️ Development Workflow

### Current Status

✅ **Completed**:
- Project structure set up
- Core data models with 55+ tests
- Pytest configuration with fixtures
- Development tools configured

🚧 **In Progress**:
- Extracting utilities from legacy code
- Setting up JiraClient with tests
- Setting up LLMClient with tests

📋 **Next Steps** (see FRAMEWORK_MIGRATION_PLAN.md):
1. Extract utilities (Week 1, Day 4-5)
2. Extract JiraClient (Week 2, Day 1-2)
3. Extract LLMClient (Week 2, Day 3-4)
4. Implement BaseAgent (Week 3, Day 1-2)
5. Implement first agent - StrategicPlanner (Week 3, Day 3-5)

### Code Quality Tools

```bash
# Format code with Black
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
pylint src/ai_tester

# Type checking
mypy src/ai_tester
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/implement-strategic-planner

# Make changes with tests
# ... code, code, code ...

# Run tests
pytest tests/ -v

# Commit with meaningful message
git commit -m "feat: implement StrategicPlannerAgent with tests"

# Push and create PR
git push origin feature/implement-strategic-planner
```

## 🎯 Development Principles

### 1. Test-Driven Development
- Write tests before implementation
- Aim for 80%+ code coverage
- Tests should be fast and isolated

### 2. Clean Code
- Use type hints on all public APIs
- Follow PEP 8 style guide
- Write docstrings for classes and public methods
- Keep functions small and focused

### 3. Modular Design
- Single Responsibility Principle
- Clear module boundaries
- Loose coupling, high cohesion
- Easy to mock and test

### 4. Incremental Migration
- Keep legacy code working
- Build new features in new structure
- Gradually migrate old code
- Maintain backward compatibility where needed

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-api-key-here

# Jira Configuration  
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-token

# Application Settings
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT=30
```

### pytest.ini (already configured in pyproject.toml)

Key settings:
- Test discovery in `tests/` directory
- Coverage reporting enabled
- Custom markers for test organization
- Verbose output by default

## 📊 Current Test Coverage

```
Module                          Statements    Coverage
---------------------------------------------------
src/ai_tester/core/models.py         150       100%
---------------------------------------------------
TOTAL                                150       100%
```

Goal: Maintain 80%+ coverage as we build out the framework.

## 🤝 Contributing

### Adding New Features

1. **Read the migration plan** - Understand the architecture
2. **Write tests first** - Follow TDD
3. **Implement feature** - Make tests pass
4. **Update documentation** - Keep docs current
5. **Run full test suite** - Ensure nothing breaks

### Adding New Tests

1. Create test file in appropriate directory
2. Use fixtures from `conftest.py`
3. Follow naming convention: `test_*.py`
4. Group related tests in classes
5. Use descriptive test names

## 🐛 Troubleshooting

### Tests Failing

```bash
# Run specific failing test with verbose output
pytest tests/path/to/test.py::test_name -vv

# Run with debugging
pytest tests/ --pdb

# Show local variables on failure
pytest tests/ -l
```

### Import Errors

```bash
# Reinstall package in editable mode
pip install -e .

# Verify installation
python -c "import ai_tester; print(ai_tester.__file__)"
```

### Coverage Not Working

```bash
# Install coverage plugin
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=src/ai_tester
```

## 📞 Support

- **Documentation**: See `docs/` directory
- **Migration Guide**: `FRAMEWORK_MIGRATION_PLAN.md`
- **Original Code**: See `legacy/` directory
- **Issues**: Check existing tests for examples

## 📈 Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅ Started
- [x] Project structure
- [x] Core models with tests
- [ ] Utilities extraction
- [ ] JiraClient with tests
- [ ] LLMClient with tests

### Phase 2: Multi-Agent (Weeks 3-4)
- [ ] BaseAgent implementation
- [ ] StrategicPlanner agent
- [ ] Evaluator agent
- [ ] Coverage validator

### Phase 3: Integration (Weeks 5-6)
- [ ] Orchestrators
- [ ] Legacy adapter
- [ ] End-to-end tests

### Phase 4: Advanced Features (Weeks 7+)
- [ ] Critic agent
- [ ] Refiner agent
- [ ] Complete multi-agent workflows

## 🎉 Getting Started

Ready to begin? Follow these steps:

1. ✅ **Verify setup** - Run `python setup_and_test.py`
2. 📖 **Read the plan** - Open `FRAMEWORK_MIGRATION_PLAN.md`
3. 🧪 **Study the tests** - Look at `tests/core/test_models.py`
4. 💻 **Start coding** - Begin with Week 1 tasks

**Happy coding! 🚀**

---

**Version**: 3.0.0  
**Status**: Active Development  
**Last Updated**: November 2025
