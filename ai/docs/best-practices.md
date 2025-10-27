# Python Development Workflow Best Practices

## Overview
This specification defines the standardized Python development workflow for this project using uv, Docker, and quality tools. This document serves as context for Claude Code and other development tools.

## Technology Stack
- **Python**: 3.10+ (required by MCP framework)
- **Package Manager**: uv
- **Container**: Docker
- **Testing**: pytest with in-memory SQLite databases
- **Linting/Formatting**: ruff
- **Type Checking**: mypy
- **Git Hooks**: pre-commit
- **Framework**: FastMCP (Model Context Protocol)

## Core Commands

### Initial Setup (one-time)
```bash
# Install dependencies
uv sync

# Setup development environment
uv run setup-dev

# Run python scripts
uv run python
```

### Docker Commands
```bash
# Build development image
docker-compose build

# Run development container
docker-compose up

# Run tests in container
docker-compose run app uv run test
```

## Testing Guidelines

### Running Tests
```bash
# Install test dependencies
uv sync --extra dev

# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_vat_rounding.py -v

# Run specific test
uv run pytest tests/test_vat_rounding.py::TestSwedishVATRounding::test_failing_case_1006_53_sek -v

# Run tests in Docker (if using Docker)
docker-compose run app uv run pytest
```

### Testing Philosophy

**In-Memory Database Testing:**
- All tests use `:memory:` SQLite databases
- **Zero production data risk** - no writes to actual database
- Fresh database for each test (perfect isolation)
- Fast execution (milliseconds per test)

**Test Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures (shared test setup)
├── test_vat_rounding.py     # VAT compliance tests
└── README.md                # Test documentation
```

**Key Fixtures** (in `conftest.py`):
- `test_db` - Fresh in-memory database with full schema
- `accounting_service` - AccountingService instance with test DB
- `sample_voucher` - Pre-created voucher for testing

**Writing New Tests:**
```python
def test_my_feature(accounting_service, sample_voucher):
    # Use accounting_service with in-memory DB
    result = accounting_service.some_method(sample_voucher)

    # Assert expected behavior
    assert result == expected_value

    # No cleanup needed - in-memory DB auto-destroyed
```

### Test Coverage Areas

**Current Coverage:**
1. **Swedish VAT Compliance**
   - Multi-rate VAT (25%, 12%, 6%, 0%)
   - Whole-number rounding per Skatteverket (22 kap. 1 § SFF)
   - Account 3740 (Öresutjämning) adjustments
   - Edge cases (tiny amounts, large amounts)

2. **Floating-Point Precision**
   - Tolerance-based comparisons
   - Balance validation

3. **Database Operations**
   - In-memory database lifecycle
   - Table creation and schema
   - Journal entry creation

**See `tests/README.md` for detailed test documentation.**

### Adding Dependencies
```bash
# Add production dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Sync dependencies after changes
uv sync
```

## Development Workflow

1. **Start Development**: Run `tree` to see current project structure
2. **Install Dependencies**: Run `uv sync --extra dev` if new dependencies are added
3. **Code**: Write code following type hints and docstrings
4. **Test Frequently**: Run `uv run pytest tests/ -v` during development
5. **Write Tests**: Add tests to `tests/` for new features
   - Use in-memory database fixtures
   - Follow existing test patterns in `tests/test_vat_rounding.py`
   - See `tests/README.md` for guidance
6. **Code Review**: After completing implementation, run CodeRabbit (see CodeRabbit Usage below)
7. **Quality Check**: Always run quality sequence after fixing CodeRabbit issues and before committing:
   ```bash
   uv run ruff check . --fix && uv run ruff format . && uv run mypy src/
   ```
8. **Test Again**: Run `uv run pytest tests/ -v` to ensure fixes didn't break anything
9. **Commit**: Pre-commit hooks will run automatically (run `uv run setup-dev` first if not set up)

```bash
# Run tests
uv run pytest

# Individual quality commands
uv run ruff check .       # Check code style (lint)
uv run ruff format .      # Format code
uv run mypy src/          # Type checking

# Auto-fix linting issues
uv run ruff check . --fix

# Quality check sequence (run all three)
uv run ruff check . && uv run ruff format . && uv run mypy src/
```


## Claude Code - CodeRabbit Integration

**When to Run CodeRabbit (Claude must follow):**

1. **After implementing any feature or Story** - Automatically run CodeRabbit review
2. **When user explicitly requests** - "Run code review" or similar
3. **Before marking work complete** - Always review before saying "done"

**How Claude Should Run CodeRabbit:**

```bash
# Always use this command
coderabbit --prompt-only
```

**Claude's Workflow:**
1. Complete the implementation as requested
2. Run `coderabbit --prompt-only` in the background (let it take as long as needed)
3. Wait for CodeRabbit to complete (7-30 minutes typical)
4. Read the output and create a task list of issues
5. Fix each issue systematically
6. Run quality checks after fixes
7. Run tests to verify fixes
8. Report completion to user

**Important:**
- ALWAYS run CodeRabbit in the background after completing implementation
- NEVER skip CodeRabbit review even if user doesn't mention it
- Run in the background to avoid blocking
- Fix ALL issues found before considering work complete

**Review Scope Options:**
```bash
# Review only uncommitted changes (faster)
coderabbit --type uncommitted --prompt-only

# Review only committed changes
coderabbit --type committed --prompt-only

# Review against specific branch
coderabbit --base develop --prompt-only
```

**Key Points:**
- Use `--prompt-only` flag for AI-optimized output
- Avoid blocking by running in the background, CodeRabbit reviews take 7-30 minutes depending on changes
- For smaller reviews: Use `--type uncommitted` or work on smaller feature branches

## Important Notes

- All commands assume you're in the project root directory
- Use `uv run` prefix for all Python commands to ensure correct environment
- Docker containers should use the same uv commands for consistency
- Pre-commit hooks enforce code quality automatically

### UV Limitations
- `tool.uv.scripts` is not yet supported by uv
- Use direct `uv run` commands instead of script shortcuts
- Quality checks must be run as individual commands or chained with `&&`

### Hatchling Configuration
Required for package discovery when using src layout:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/your_package"]
```

### Common Issues
- **"Unable to determine which files to ship"**: Add hatchling wheel target configuration
- **Missing newlines**: Use `uv run ruff check . --fix` to auto-fix
- **Type errors**: Add return type annotations (`-> None` for functions without returns)
- **Tests failing**: Ensure `uv sync --extra dev` has been run
- **In-memory DB issues**: Each test gets fresh database - check fixture usage in `conftest.py`

## Project-Specific Patterns

### Swedish Accounting Compliance

**VAT Handling:**
- Always use `AccountingService.add_swedish_vat_entries()` for VAT transactions
- VAT amounts are automatically rounded to whole SEK (Skatteverket requirement)
- Rounding adjustments use account 3740 (Öres- och kronutjämning)
- Supports all Swedish VAT rates: 25%, 12%, 6%, 0%

**Floating-Point Comparisons:**
- Never use `==` or `!=` for currency amounts
- Always use tolerance: `abs(a - b) < 0.01` (1 öre tolerance)
- Example in `post_voucher()`: checks balance with 0.01 SEK tolerance

**Database Operations:**
- Production DB: File-based at `~/.mcp-accounting-server/invoices.db`
- Test DB: In-memory (`:memory:`) - auto-destroyed after each test
- Use `with db.get_connection() as conn:` context manager
- For tests: Use fixtures from `conftest.py`

### Service Layer Architecture

**Layering:**
- Server (`server.py`): Thin presentation layer, MCP tools
- Services (`src/modules/*/`): Business logic, reusable methods
- Database (`src/database/`): Data persistence
- Models (`src/models/`): Domain objects

**Best Practice:**
- Keep business logic in service layer, not server
- Server methods should orchestrate, not implement
- Example: `add_swedish_vat_entries()` in AccountingService, called by server

### Documentation

**Always Update:**
1. `ai/hist/diary.mdx` - Development history and decisions
2. `CLAUDE.md` - Project overview for AI assistants
3. `ai/docs/best-practices.md` - This file
4. Docstrings in code for new methods

**Testing Documentation:**
- See `tests/README.md` for complete test suite documentation
- Tests serve as usage examples

## Security: TOTP-Protected Operations

### Overview

**Critical Security Policy**: ALL voucher annotations require TOTP (Time-based One-Time Password) two-factor authentication. This ensures bank-level security for financial audit trail modifications.

### TOTP-Protected MCP Tools

**Public API (requires TOTP):**
- `add_secure_voucher_annotation()` - Add notes/corrections to vouchers
- `supersede_voucher()` - Replace incorrect vouchers
- `void_voucher()` - Mark vouchers as void

**Removed for Security:**
- ❌ `add_voucher_annotation()` - **REMOVED** (bypassed TOTP protection)

### Security Features

**Rate Limiting:**
- Max 3 TOTP attempts per 30 seconds
- Prevents brute force attacks

**Account Lockout:**
- 15-minute lockout after 5 failed attempts
- Use backup codes for emergency access

**Backup Codes:**
- 8 single-use emergency codes generated during setup
- Store securely, regenerate via `python src/totp_setup/setup_totp.py`

**Audit Trail:**
- Every TOTP verification logged
- Complete history via `get_voucher_history()`

### Common TOTP Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| `INVALID_TOTP` | Wrong code | Check Google Authenticator |
| `RATE_LIMITED` | Too many attempts | Wait 30 seconds |
| `ACCOUNT_LOCKED` | 5 failed attempts | Wait 15 min or use backup code |
| `EXPIRED_CODE` | Code expired | Codes change every 30 seconds |

### Emergency Recovery

**Account Locked:**
1. Wait 15 minutes for auto-unlock
2. OR use backup code immediately
3. Contact admin if all backups used

**Lost TOTP Device:**
1. Use remaining backup codes
2. Run `python src/totp_setup/setup_totp.py` to regenerate
3. Set up new Google Authenticator with QR code

### Usage Examples

**Secure Annotation:**
```python
# ✅ Correct - requires TOTP
add_secure_voucher_annotation(
    voucher_id=123,
    annotation_type="NOTE",
    message="Corrected amount calculation",
    user_email="user@example.com",
    totp_code="123456"
)
```

**Voucher Supersession:**
```python
# ✅ Correct - uses dedicated method
supersede_voucher(
    original_voucher_id=123,
    replacement_voucher_id=124,
    reason="Fixed calculation error",
    user_email="user@example.com",
    totp_code="123456"
)
```

### Best Practices

1. **Never bypass TOTP** - Security is not optional
2. **Document reasons** - Be specific in annotation messages
3. **Use correct methods** - `supersede_voucher()` for replacements
4. **Protect backup codes** - Store securely, never share
5. **Regular security audits** - Review TOTP verification logs

**See diary entry 2025-01-14 for implementation history.**
