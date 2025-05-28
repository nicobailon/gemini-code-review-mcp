**Overall PRD summary: (2-3 sentences max)**
This tool automates the generation of code review context by parsing project documentation and git changes. It creates structured templates for AI-assisted code reviews.

**Total Number of phases in Task List: 3**

**Current phase number: 2.0**
**Previous phase completed: 1.0 Set up project structure**

**Next phase: 3.0 Add MCP integration**

**Current phase description: "Implement core parsing logic"**

**Subtasks completed in current phase: ['2.1', '2.2', '2.3']**

**/path/to/test/project**
**<file_tree>**
/path/to/test/project
├── src/
│   ├── parser.py
│   └── server.py
├── tests/
│   └── test_parser.py
└── README.md
**</file_tree>**

**<files_changed>**
**File: src/parser.py**
**```python**
def parse_task_list(content):
    # Implementation here
    pass
**```**
**</files_changed>**

**<user_instructions>**
We have just completed phase #2.0: "Implement core parsing logic".

Based on the PRD, the completed phase, all subtasks that were finished in that phase, and the files changed, your job is to conduct a code review and output your code review feedback for the completed phase. Identify specific lines or files that are concerning when appropriate.
**</user_instructions>**