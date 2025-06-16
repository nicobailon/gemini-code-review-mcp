# Python Type Safety & Development Guidelines

## Type Safety Rules

**FORBIDDEN Anti-Patterns:**
```python
# ❌ NEVER: Type widening, Any, type: ignore, removing constraints
def process(data: Any) -> Any: ...  # NO
user: Any = get_user()  # NO
result = operation()  # type: ignore  # NO
Status = str  # NO - use Literal/Enum
```

**REQUIRED Practices:**
```python
# ✅ ALWAYS: Precise types
from typing import Literal, NewType, TypedDict, TypeGuard, Protocol
from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"

class UserData(TypedDict):
    email: str
    role: UserRole
    status: Literal["active", "inactive"]

UserId = NewType('UserId', str)
Email = NewType('Email', str)

def is_user_data(obj: object) -> TypeGuard[UserData]:
    return isinstance(obj, dict) and "email" in obj
```

## Resolution Protocol

1. **Analyze**: Missing annotations, generic constraints, Union guards, Protocols, Optional handling
2. **Fix (in order)**: Explicit annotations → TypeGuards → Generic constraints → Protocols → Literals → TypedDict/dataclasses
3. **Validate**: `mypy --strict` zero errors, PyLance clean, business constraints in types
4. **Last resort**: Document failures, try TypeVar bounds, Protocols, overloads, guards

## TDD Protocol

### Phase 1: Test First
```python
# Write tests including type validation
def test_function_signature():
    hints = get_type_hints(my_function)
    assert hints['return'] == UserData
    
def test_type_safety():
    with pytest.raises(TypeError):
        process_user("invalid")
```
**State**: "Doing TDD - do NOT create mock implementations"

### Phase 2-4: Validate → Implement → Verify
- Run tests (must fail) → Write code → All tests/types pass → Runtime type verification

## Pydantic/Dataclass Standards

```python
# ✅ Precise Pydantic
class User(BaseModel):
    id: UserId
    email: Email = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    role: UserRole
    status: Literal["active", "inactive", "pending"]
    
    @validator('email')
    def validate_email(cls, v):
        return Email(v.lower())

# ✅ Type-safe dataclass
@dataclass(frozen=True)
class Config:
    api_url: str
    timeout: int = Field(gt=0)
```

## PyLance Error Solutions

1. **"Argument missing"**: Use overloads or proper defaults
2. **"Cannot assign to method"**: Use delegation/composition
3. **"Incompatible return"**: Return complete, valid data
4. **Debug with**: `reveal_type()`, intermediate annotations, cast with runtime check

## Runtime Validation

```python
from typeguard import typechecked
from beartype import beartype

@typechecked  # Or @beartype for zero-overhead
def process_user(user_data: UserData) -> ProcessedUser:
    return ProcessedUser(...)
```

## Quality Gates
- `mypy --strict` passes
- PyLance no errors
- No Any/object/broad types
- All tests pass including type validation
- Business constraints in types

**Core principle**: Type widening is technical debt. Any/ignore = failure.

---

# Project Structure Guidelines

## File Size Limits

**Thresholds:**
- **> 200 lines**: Review for separation
- **> 400 lines**: Consider splitting
- **> 600 lines**: Plan refactoring
- **> 1000 lines**: STOP - refactor immediately

## Organization Patterns

```
# ✅ Domain-Driven
src/
├── user/
│   ├── models.py        (<200 lines)
│   ├── services.py      (<600 lines)
│   ├── repositories.py
│   └── validators.py
├── order/
│   └── [similar structure]
└── shared/
    └── utils/

# ✅ Layer-Based
src/
├── models/
├── services/
├── repositories/
└── api/
```

## Refactoring Process

1. **Analyze**: Identify responsibilities, domain groupings
2. **Separate**: Domain → Layer → Feature → Utility → Abstract/concrete
3. **Validate**: Test coverage maintained, no circular imports
4. **Monitor**: `find src -name "*.py" -exec wc -l {} + | awk '$1 > 600 {print}'`

---

# Development Environment

## Package Management

**Development:**
```bash
# Always in venv
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/
```

**End Users:**
```bash
uvx task-list-code-review-mcp /path
```

**Decision Tree:**
- Testing/developing? → venv → pip install -e ".[dev]"
- End user? → uvx
- Externally-managed error? → Create venv
- ModuleNotFoundError? → pip install -e ".[dev]"

## MCP Server Setup

```bash
# CORRECT (note the -- separator)
claude mcp add task-list-reviewer -- uv run python src/server.py

# Management
claude mcp list
claude mcp get task-list-reviewer
claude mcp remove task-list-reviewer
```

## Running Tests - OFFICIAL METHOD

**IMPORTANT**: Use this method consistently across all sessions to run tests.

### For Development (Recommended):
```bash
# STEP 1: Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# STEP 2: Install package with dev dependencies
pip install -e ".[dev]"

# STEP 3: Run tests
python -m pytest tests/        # Run all tests
python -m pytest tests/ -v     # Verbose output
python -m pytest tests/test_critical.py  # Run specific test file
```

### Alternative with uvx (for isolated testing):
```bash
# Only use if you need isolated environment testing
uvx --with gemini-code-review-mcp[dev] pytest tests/
```

### Why This Method:
1. **Virtual Environment**: Ensures clean, isolated dependencies
2. **Editable Install**: `-e` flag means changes to source code are immediately reflected
3. **Dev Dependencies**: `[dev]` includes pytest, pytest-mock, pytest-asyncio
4. **Consistent**: Works the same way across all platforms and Python versions

### DO NOT USE:
- ❌ `pytest` directly without `python -m`
- ❌ System Python without virtual environment
- ❌ Mixed approaches between sessions

## Testing Multi-Step Workflows

```python
# Mock ALL external calls in workflow
with patch('meta_prompt.send_to_gemini') as mock_meta:
    with patch('review.send_to_gemini') as mock_review:
        mock_meta.return_value = "meta prompt"
        mock_review.return_value = "review"
        
        result = generate_ai_code_review(project_path=path)
        
        # Both called in full workflow
        mock_meta.assert_called_once()
        mock_review.assert_called_once()
```

## Type Checking Protocol

### Pylance/Pyright Type Checking

**Setup:**
```bash
# Create venv and install dev dependencies
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

**Type Checking:**
Pylance in VS Code uses Pyright under the hood. Run the same type checks via command line:

```bash
# Run pyright type checking (equivalent to Pylance)
source venv/bin/activate && pyright src/

# Check specific file
source venv/bin/activate && pyright src/generate_code_review_context.py

# Get type checking statistics
source venv/bin/activate && pyright src/ --stats
```

**Type Checking Status:**
- 🎯 **Goal**: Match Pylance's 350+ problems detected in VS Code  
- ✅ **SUCCESS**: Pyright now detects 365 issues for main file (MATCH ACHIEVED!)
- 📊 **Full project**: 732 total type checking issues across all src files
- ⚙️ **Configuration**: pyrightconfig.json with strict mode matches Pylance exactly

**Common Pyright/Pylance Issues:**
- **Type annotations**: Missing or incorrect type hints
- **Undefined variables**: Variables that might not be initialized
- **Type mismatches**: Incompatible types in assignments or function calls
- **Import errors**: Missing modules or circular imports
- **Possibly unbound**: Variables that might not be defined in all code paths

**Resolution Priority:**
1. Fix undefined/unbound variables  
2. Add missing type annotations
3. Resolve type mismatches
4. Fix import issues
5. Address remaining type safety issues

### Pyright Error Categories

**Type Safety Issues:**
- Missing type annotations
- Incorrect return types  
- Undefined/unbound variables
- Type compatibility errors
- Import resolution failures

**Configuration Notes:**
- Pyright configuration can be set via `pyrightconfig.json` or `pyproject.toml`
- Pylance in VS Code may use different default settings than command-line pyright
- Goal is to match Pylance's detection exactly for comprehensive type checking

## Key Reminders

- **NEVER**: Mix pip/uvx for same task, use system Python, install pytest globally
- **ALWAYS**: Check venv active, install [dev] dependencies, understand full workflow before testing
- **File organization**: Large files = missing abstractions
- **Types**: Precision now saves debugging later
- **Lint checking**: Run flake8 and pyflakes before commits
- **Delete temporary files** not part of explicit tasks

<python_environment_commands>
CRITICAL: When working with Python packages and dependencies, always consider the environment context before executing commands.

COMMON FAILURE PATTERNS TO AVOID:

1. Running `pip install` in externally-managed environments (Homebrew Python, system Python)
2. Using `python -m build` without checking if build tools are available
3. Using `uvx` with incorrect package/executable names

REQUIRED ENVIRONMENT CHECKS:
Before any Python package operations, determine:

- Is this a virtual environment? (check for venv activation)
- Is this an externally-managed environment? (Homebrew, system Python)
- Are build tools already available?

CORRECT COMMAND PATTERNS:

For building Python packages:

- In managed environments: `uvx --from build pyproject-build` (NOT `uvx build`)
- In virtual environments: `python -m build` (after `pip install build`)
- NEVER use `pip install` directly in externally-managed environments

For installing dependencies:

- Managed environments: Use `uvx`, `pipx`, or create virtual environment first
- Virtual environments: Use `pip install`
- Check error messages for suggested alternatives (like brew install)

DECISION TREE:

1. Need to build package? → Use `uvx --from build pyproject-build`
2. Need to install tool globally? → Use `pipx install` or `uvx`
3. Need to install dependency? → Check if in virtual environment first
4. Getting "externally-managed-environment" error? → Don't retry with pip, use uvx/pipx instead

Think through the environment context before executing ANY Python package command.
</python_environment_commands>

<no_unsolicited_file_creation>
**NO CREATING FILES WITHOUT PERMISSION**: Only create files explicitly requested or directly required by the task. No documentation, configs, or "nice-to-have" files without asking first.
</no_unsolicited_file_creation>