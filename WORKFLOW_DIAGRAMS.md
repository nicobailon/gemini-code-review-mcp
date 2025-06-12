# Workflow Diagrams

ASCII flow diagrams illustrating the data flow for each CLI command and MCP tool in the gemini-code-review-mcp system.

## 📝 Recent Updates (Based on Code Analysis - January 2025)

### Key Implementation Enhancements:
1. **Ask Gemini Tool**: NEW unified tool that combines file context generation with AI response in one step
2. **File-Based Context Generation**: Enhanced with `ask_gemini` tool, deprecated `generate_file_context` MCP tool
3. **Configuration Discovery**: Added import resolution for CLAUDE.md files (@import syntax)
4. **Performance**: Async operations and caching mechanisms added but not shown in original diagrams
5. **Default Behaviors**: 
   - `text_output` defaults: `false` for generate_pr_review, `true` for other tools
   - `auto_meta_prompt` defaults to `true` for enhanced experience
6. **Deprecated Features**: 
   - Branch comparison removed, use GitHub PR integration instead
   - `generate_file_context` MCP tool deprecated, use `ask_gemini` instead

### Workflow Accuracy Status:
- ✅ All main workflows updated to match current implementation (January 2025)
- ✅ Updated `ask_gemini` as the primary tool for file-based context + AI response
- ✅ Marked `generate_file_context` MCP tool as deprecated
- ✅ Added new ask_gemini Q&A workflows for both CLI and MCP tools
- ✅ Added missing `raw_context_only` mode to `generate_pr_review` diagram
- ✅ Added meta-prompt generation step to `generate_pr_review` diagram
- ✅ Added model configuration step to code review context generation diagram
- ✅ Updated CLI commands section with correct entry points
- ⚠️ Additional features exist in code not shown in diagrams (caching, async, import resolution)
- 📋 Testing workflow added with official method reference to CLAUDE.md

## 🚀 Key Enhancements in Current Implementation

### Ask Gemini - Unified Context + AI Response (NEW - January 2025)

**Single-Step AI Assistance**: Combines file context generation with Gemini API call in one operation.

**Flexible File Selection**: Support for specific line ranges (e.g., `file.py:10-50,100-150`) to focus on relevant code.

**In-Memory Processing**: No intermediate context files created - direct pipeline from files to AI response.

**Smart Defaults**: Automatically includes CLAUDE.md configuration and generates meta-prompts when appropriate.

**Use Cases**:
- Get instant AI feedback on specific code sections
- Debug errors with contextual understanding
- Architecture decisions with full project awareness
- Quick technical questions with optional file context

### Ask Gemini Q&A (NEW - January 2025)

**Direct AI Assistance**: Get instant answers to development questions with optional file context.

**Simplified Interface**: Single question parameter combines query and instructions naturally.

**In-Memory Processing**: File context generated on-the-fly without creating intermediate files.

**Two CLI Modes**:
- `ask-gemini`: Full-featured with file context support
- `ask-gemini-direct`: Lightweight for quick questions

**Use Cases**:
- Debug errors with specific code context
- Get implementation guidance during development
- Understand complex code sections
- Quick technical questions without context

### Auto Meta Prompt Integration

**Default Behavior Change**: `auto_meta_prompt=true` is now the default for enhanced user experience.

**Optimized Generation**: No intermediate files created during meta prompt generation - direct project analysis.

**Project-Aware Prompts**: Meta prompts now include project-specific configuration discovery (CLAUDE.md, cursor rules).

**Clean Integration**: Meta prompts embedded in `<user_instructions>` section of context files.

### Multi-Mode AI Review Support

**Three Input Modes**:
- `context_file_path`: Process existing context files
- `context_content`: Direct content processing for AI chaining
- `project_path`: Generate context and review in one operation

**Intelligent Cleanup**: Temporary files automatically cleaned up in project mode.

**Unified Processing**: All modes converge to consistent AI review generation.

## 🎯 Meta-Prompt Generation (Updated Architecture)

### Internal Helper: `generate_meta_prompt` (Enhanced Implementation - Not an MCP Tool)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ MCP Client      │───▶│ Input Validation │───▶│ Context Analysis│
│ • Claude Desktop│    │ • Check params   │    │ • Parse content │
│ • Claude Code   │    │ • Validate paths │    │ • Extract data  │
│ • AI Agent      │    │ • Enforce mutex  │    │ • Analyze scope │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Config Discovery │◀───│ Project Path    │
                       │ • CLAUDE.md files│    │ • Optional step │
                       │ • Cursor rules   │    │ • Extra context │
                       │ • Project config │    │ • Rich prompts  │
                       └──────────────────┘    └─────────────────┘
                                │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ MCP Response    │◀───│ Gemini API       │◀───│ Template Engine │
│ • Raw content   │    │ • include_format:│    │ • Priority:     │
│ • No headers    │    │   false          │    │   1. custom_    │
│ • Ready for AI  │    │ • Clean response │    │      template   │
│ • text_output   │    │ • Temperature:   │    │   2. ENV var    │
│   controls fmt  │    │   0.3 (low)      │    │   3. default    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Implementation Notes:**
- Configuration discovery is an additional feature not in original design
- Template priority system allows flexible customization
- Lower temperature (0.3) for consistent meta-prompt generation
- text_output parameter controls response format (default: false)

### Optimized Meta Prompt Analyzer (Internal)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Project Path    │───▶│ Lightweight      │───▶│ Direct Gemini   │
│ • No temp files │    │ Analysis         │    │ Analysis        │
│ • Direct scan   │    │ • Config files   │    │ • Project-aware │
│ • Scope param   │    │ • File structure │    │ • Custom prompts│
└─────────────────┘    │ • Git context    │    │ • Clean response│
                       └──────────────────┘    └─────────────────┘
                                                         │
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Ready for        │◀───│ Generated       │
                       │ Embedding        │    │ Meta-Prompt     │
                       │ • No file I/O    │    │ • Project rules │
                       │ • Single pass    │    │ • Config aware  │
                       │ • Fast response  │    │ • Type safety   │
                       └──────────────────┘    └─────────────────┘
```

## 📁 File-Based Context Generation (NEW)

### CLI: `gemini-code-review-mcp generate-file-context`

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ File Selection  │───▶│ Parse & Validate │───▶│ Token Counting  │
│ • File paths    │    │ • Parse syntax   │    │ • Estimate size │
│ • Line ranges   │    │ • Validate paths │    │ • Check limits  │
│ • project.py:10-50│  │ • Check exists   │    │ • 200k max      │
│ • utils.py      │    │ • Extract ranges │    │ • Priority order│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Context Output  │◀───│ Context Builder  │◀───│ File Reading    │
│ • Selected files│    │ • Format template│    │ • Read content  │
│ • Line numbers  │    │ • Add metadata   │    │ • Apply ranges  │
│ • User instruct │    │ • Include configs│    │ • Format code   │
│ • Token report  │    │ • Embed prompts  │    │ • Handle errors │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲
                       ┌──────────────────┐
                       │ Optional Features│
                       │ • CLAUDE.md      │
                       │ • Cursor rules   │
                       │ • Meta-prompt    │
                       └──────────────────┘
```

### MCP Tool: `generate_file_context` (DEPRECATED - Use `ask_gemini` instead)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ MCP Request     │───▶│ DEPRECATED       │───▶│ File Selection  │
│ • file_selections│   │ • Shows warning  │    │ • Parse paths   │
│ • project_path  │    │ • Works for      │    │ • Line ranges   │
│ • user_instruct │    │   compatibility │    │ • Resolve paths │
│ • auto_meta=true│    │ • Use ask_gemini │    │ • Check access  │
│ • text_output   │    │   for AI response│    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Token Management │◀───│ Content Reading │
                       │ • Count tokens   │    │ • Read files    │
                       │ • 200k limit     │    │ • Extract lines │
                       │ • Priority order │    │ • Format with # │
                       │ • Track excluded │    │ • Error handling│
                       └──────────────────┘    └─────────────────┘
                                │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Auto Meta       │◀───│ Feature Flags    │◀───│ Configuration   │
│ Prompt Check    │    │ • auto_meta_     │    │ Discovery       │
│ • Default: true │    │   prompt=true    │    │ • CLAUDE.md     │
│ • File-aware    │    │ • include_configs│    │ • Cursor rules  │
│ • Custom prompts│    │ • Token aware    │    │ • Project config│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Output Mode     │◀───│ Template Builder │◀───│ Context Assembly│
│ • File path     │    │ • File summary   │    │ • Selected files│
│ • Text content  │    │ • Project path   │    │ • Configurations│
│ • Excluded list │    │ • Config context │    │ • User instruct │
│ • Token report  │    │ • User instruct  │    │ • Excluded info │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Features:

1. **Flexible File Selection**:
   - Simple paths: `src/main.py`
   - With line ranges: `src/utils.py:10-50,100-150`
   - Multiple files in single request
   - Automatic path resolution

2. **Token Management**:
   - 200k LLM token limit enforcement
   - Files processed in user-specified order
   - Clear reporting of excluded files
   - Token counting before inclusion

3. **Integration Points**:
   - Reuses existing configuration discovery
   - Integrates with meta-prompt generation
   - Compatible with AI review workflow
   - Same output format as git-based context

4. **Error Handling**:
   - File not found errors
   - Invalid line ranges
   - Permission errors
   - Token limit exceeded

## 🤖 Ask Gemini - Direct Q&A with File Context (NEW)

### CLI: `ask-gemini` and `ask-gemini-direct`

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ User Question   │───▶│ Parse Arguments  │───▶│ File Selection  │
│ • Natural query │    │ • Question text  │    │ • Optional files│
│ • All context   │    │ • File paths     │    │ • Line ranges   │
│ • Single input  │    │ • Options parse  │    │ • Validate paths│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Gemini Response │◀───│ Send to Gemini   │◀───│ Context Builder │
│ • Direct answer │    │ • Combined prompt│    │ • File content  │
│ • Code examples │    │ • Temperature    │    │ • CLAUDE.md     │
│ • Explanations  │    │ • Model select   │    │ • Question text │
│ • To stdout/file│    │ • Stream response│    │ • In-memory     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### MCP Tool: `ask_gemini`

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ MCP Request     │───▶│ Input Validation │───▶│ File Context    │
│ • user_         │    │ • Validate input │    │ Generation      │
│   instructions  │    │ • Normalize files│    │ • In-memory     │
│ • file_selections│   │ • Check empty    │    │ • No temp files │
│ • project_path  │    │   case: files OR │    │ • Config discovery│
│ • temperature   │    │   instructions   │    │ • Auto meta prompt│
│ • model         │    │ • Set defaults   │    │ • Token management│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ MCP Response    │◀───│ Gemini API Call  │◀───│ Context Assembly│
│ • Text answer   │    │ • send_to_gemini │    │ • File content  │
│   (default)     │    │   _for_review    │    │ • User instruct │
│ • Or file path  │    │ • Model config   │    │ • CLAUDE.md     │
│   if text_output│    │ • Temperature    │    │ • Meta-prompt   │
│   =false        │    │ • Thinking budget│    │ • Clean format  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Features:

1. **Simplified Interface**:
   - Single question parameter includes all instructions
   - No separate instructions flag needed
   - Natural language queries with context

2. **In-Memory Processing**:
   - File context generated on-the-fly
   - No intermediate files created
   - Direct pipeline to Gemini API

3. **Two CLI Modes**:
   - `ask-gemini`: Full featured with file context support
   - `ask-gemini-direct`: Quick questions without files

4. **Use Cases**:
   - Code explanation with specific files
   - Debugging assistance with context
   - Implementation guidance
   - Quick technical questions

## 📋 Code Review Context Generation

### CLI: `gemini-code-review-mcp` (Traditional Workflow)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Project Input   │───▶│ Task Discovery   │───▶│ Scope Detection │
│ • Project path  │    │ • Find tasks/*.md│    │ • Phase analysis│
│ • Task list     │    │ • Auto-select    │    │ • Completion    │
│ • Scope params  │    │ • Parse progress │    │ • Smart default │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Context File    │◀───│ Context Builder  │◀───│ Git Analysis    │
│ • Markdown      │    │ • Combine data   │    │ • File diffs    │
│ • Timestamped   │    │ • Format output  │    │ • Status info   │
│ • Review ready  │    │ • Add metadata   │    │ • Branch data   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲
                       ┌──────────────────┐
                       │ Configuration    │
                       │ • CLAUDE.md      │
                       │ • Cursor rules   │
                       │ • PRD context    │
                       └──────────────────┘
```

### Internal Process: Code Review Context Generation (Enhanced with Auto Meta Prompt)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ MCP Request     │───▶│ Parameter Parse  │───▶│ Model Config    │
│ • project_path  │    │ • Validate input │    │ • Load config   │
│ • scope         │    │ • Set defaults   │    │ • Detect caps:  │
│ • auto_meta_    │    │ • Check paths    │    │   - URL context │
│   prompt=true   │    │ • Temperature    │    │   - Grounding   │
└─────────────────┘    └──────────────────┘    │   - Thinking    │
                                               └─────────────────┘
                                                         │
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Auto Meta        │◀───│ Check Feature   │
                       │ Prompt Check     │    │ Flags           │
                       │ • auto_meta_     │    │ • DISABLE_URL_  │
                       │   prompt=true    │    │   CONTEXT       │
                       │   (default)      │    │ • DISABLE_      │
                       │ • Optional step  │    │   GROUNDING     │
                       └──────────────────┘    └─────────────────┘
                                │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Meta Prompt     │◀───│ Meta Prompt      │◀───│ Project Analysis│
│ Generation      │    │ Analyzer         │    │ • Config discovery│
│ • Optimized     │    │ • No temp files  │    │ • File structure│
│ • Project-aware │    │ • Gemini API     │    │ • Git context   │
│ • Custom prompt │    │ • Clean response │    │ • Task progress │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Output Mode     │◀───│ Context Builder  │◀───│ Data Collection │
│ • File path     │    │ • Embed meta     │    │ • Git diffs     │
│ • Text content  │    │   prompt in      │    │ • Task progress │
│ • Enhanced with │    │   <user_instr>   │    │ • Config files  │
│   meta prompt   │    │ • Format output  │    │ • Meta context  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🤖 AI Code Review Generation

### CLI: `review-with-ai`

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Context File    │───▶│ File Validation  │───▶│ Prompt Builder  │
│ • .md file      │    │ • Check exists   │    │ • Load template │
│ • Review data   │    │ • Parse content  │    │ • Insert context│
│ • Metadata      │    │ • Extract info   │    │ • Custom prompt │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Review File     │◀───│ Response Parser  │◀───│ Gemini API      │
│ • AI feedback   │    │ • Format output  │    │ • Send request  │
│ • Timestamped   │    │ • Add metadata   │    │ • Model config  │
│ • Markdown      │    │ • Structure data │    │ • Temperature   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### MCP Tool: `generate_ai_code_review` (Enhanced Multi-Mode)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ MCP Input       │───▶│ Input Validation │───▶│ Mode Detection  │
│ • context_file  │    │ • Validate params│    │ • File mode     │
│ • context_content│   │ • Check paths    │    │ • Content mode  │
│ • project_path  │    │ • Mutex check    │    │ • Project mode  │
│ • auto_meta_    │    │ • Set defaults   │    │ • Auto meta     │
│   prompt=true   │    │                  │    │   prompt check  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
        ┌─────────────────────────────────────────────────────┐
        │                    MODE BRANCHES                    │
        └─────────────────────────────────────────────────────┘
                 │                    │                    │
        ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
        │ File Mode       │  │ Content Mode    │  │ Project Mode    │
        │ • Load file     │  │ • Direct content│  │ • Generate ctx  │
        │ • Read context  │  │ • Immediate use │  │ • Meta prompt   │
        │ • Apply prompt  │  │ • Apply prompt  │  │ • Temp cleanup  │
        └─────────────────┘  └─────────────────┘  └─────────────────┘
                 │                    │                    │
        ┌─────────────────────────────────────────────────────┐
        │                 UNIFIED PROCESSING                   │
        └─────────────────────────────────────────────────────┘
                                  │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Output Mode     │◀───│ Response Handler │◀───│ Gemini API      │
│ • File path     │    │ • Parse response │    │ • Send request  │
│ • Text content  │    │ • Format output  │    │ • Model config  │
│ • AI chaining   │    │ • Add metadata   │    │ • Temperature   │
│ • Clean cleanup │    │ • File cleanup   │    │ • Custom prompt │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔗 Branch Comparison (Deprecated - Use GitHub PR Integration)

Branch comparison functionality has been consolidated into the GitHub PR integration. Instead of using dedicated branch comparison tools, create a GitHub PR and use the `generate_pr_review` tool for more comprehensive analysis including:

- Automated branch detection and comparison
- PR metadata and context
- GitHub-native diff analysis
- Enhanced collaboration features
- Better CI/CD integration

## 🔗 GitHub PR Integration

### MCP Tool: `generate_pr_review` (Enhanced with In-Memory Processing)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ PR URL Input    │───▶│ Parameter Parse  │───▶│ Meta-Prompt Gen │
│ • github_pr_url │    │ • Validate input │    │ • Check auto_   │
│ • project_path  │    │ • Check required │    │   meta_prompt   │
│ • create_context│    │ • Set defaults   │    │ • Generate if   │
│   _file=false   │    │ • Auto meta      │    │   enabled       │
│   (default)     │    │   prompt=true    │    │ • Fallback to   │
│ • text_output=  │    │ • text_output=   │    │   template      │
│   false (default)│    │   false (default)│    │ • Optional step │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Mode Detection   │───▶│ 3 Processing    │
                       │ • raw_context_   │    │ Modes:          │
                       │   only: Raw ctx  │    │ 1. DEFAULT      │
                       │ • create_context │    │ 2. CONTEXT FILE │
                       │   _file: Save ctx│    │ 3. RAW CONTEXT  │
                       │ • DEFAULT: In-   │    │                 │
                       │   memory + AI    │    │                 │
                       └──────────────────┘    └─────────────────┘
                                                         │
        ┌─────────────────────────────────────────────────────────┐
        │                    MODE BRANCHES                         │
        └─────────────────────────────────────────────────────────┘
                 │                    │                    │
        ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
        │ DEFAULT MODE    │  │ CONTEXT FILE    │  │ RAW CONTEXT     │
        │ (NEW BEHAVIOR)  │  │ MODE            │  │ ONLY MODE       │
        │ • In-memory     │  │ • File creation │  │ • Context gen   │
        │   context gen   │  │ • Traditional   │  │ • No AI review  │
        │ • NO context    │  │ • Legacy compat │  │ • Raw output    │
        │   files saved   │  │ • Debug/inspect │  │ • For chaining  │
        └─────────────────┘  └─────────────────┘  └─────────────────┘
                 │                    │                    │
        ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
        │ GitHub API      │  │ GitHub API      │  │ GitHub API      │
        │ • Fetch PR data │  │ • Fetch PR data │  │ • Fetch PR data │
        │ • Extract info  │  │ • Extract info  │  │ • Extract info  │
        │ • Generate ctx  │  │ • Generate ctx  │  │ • Generate ctx  │
        │   in memory     │  │ • Save context  │  │ • Save context  │
        └─────────────────┘  └─────────────────┘  └─────────────────┘
                 │                    │                    │
        ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
        │ Direct to AI    │  │ Context File    │  │ Context Output  │
        │ • Pass context  │  │ • .md output    │  │ • Context file  │
        │   to Gemini     │  │ • PR metadata   │  │   or text       │
        │ • Auto meta     │  │ • Review ready  │  │ • No AI process │
        │   prompt        │  │ • Structured    │  │ • Based on      │
        │ • Clean process │  │ • Inspectable   │  │   text_output   │
        └─────────────────┘  └─────────────────┘  └─────────────────┘
                 │                    │                    │
        ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
        │ AI Review File  │  │ No AI Review    │  │ Raw Context     │
        │ • pr-review-    │  │ • Context only  │  │ • code-review-  │
        │   feedback-*.md │  │ • User can then │  │   context-*.md  │
        │ • Only output   │  │   call generate │  │ • Or direct text│
        │ • Clean result  │  │   _ai_code_     │  │ • Ready for AI  │
        │ • No artifacts  │  │   review        │  │   agent chain   │
        └─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 🔄 Combined Workflow Patterns

### Pattern 1: File-Based Q&A with ask_gemini (RECOMMENDED)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Debugging Task  │───▶│ ask_gemini       │───▶│ Direct AI Answer│
│ • Specific files│    │ • user_instruct: │    │ • Bug analysis  │
│ • Error in      │    │   "Fix null ref  │    │ • Fix suggest   │
│   utils.py:45-90│    │    error"        │    │ • Code patches  │
│ • Related code  │    │ • file_selections│    │ • Explanation   │
│   main.py:10-30 │    │ • Single step    │    │ • No temp files │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Pattern 1b: Legacy File Context Generation (DEPRECATED)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Context Only    │───▶│ generate_file_   │───▶│ Context Output  │
│ • Debug/inspect │    │ context          │    │ • No AI call    │
│ • Manual review │    │ • DEPRECATED     │    │ • Context file  │
│ • Share context │    │ • file_selections│    │ • Manual review │
│                 │    │ • Use ask_gemini │    │ • Use CLI instead│
└─────────────────┘    │   for AI response│    └─────────────────┘
                       └──────────────────┘
```

### Pattern 2: Feature Implementation Guidance (NEW)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ New Feature     │───▶│ File Context Gen │───▶│ Save Context    │
│ Planning        │    │ • Multiple files │    │ File            │
│ • API endpoints │    │ • Full files     │    │ • Review ready  │
│ • Data models   │    │ • Instructions:  │    │ • Share with    │
│ • UI components │    │   "Add user auth"│    │   team          │
│ • No git changes│    │ • auto_meta_     │    │ • Iterate on    │
│                 │    │   prompt=true    │    │   design        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ AI Review       │◀───│ generate_ai_     │◀───│ Context File    │
│ • Architecture  │    │ code_review      │    │ • All relevant  │
│ • Best practices│    │ • context_file   │    │   code included │
│ • Security      │    │ • Custom prompts │    │ • Meta-prompt   │
│ • Implementation│    │ • Gemini analysis│    │   optimized     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Pattern 3: Enhanced MCP PR Review (NEW DEFAULT - In-Memory Processing)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Single MCP Call │───▶│ generate_pr_     │───▶│ In-Memory       │
│ • github_pr_url │    │ review           │    │ Context Gen     │
│ • project_path  │    │ • text_output=   │    │ • GitHub API    │
│ • Clean workflow│    │   false (default)│    │ • PR analysis   │
│ • No temp files │    │ • create_context │    │ • Config disc   │
│                 │    │   _file=false    │    │ • Auto meta     │
└─────────────────┘    │   (default)      │    │ • NO files      │
                       └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ AI Review File  │◀───│ Direct Gemini    │◀───│ Memory Context  │
│ • pr-review-    │    │ Processing       │    │ • Full PR data  │
│   feedback-*.md │    │ • Meta prompts   │    │ • Project config│
│ • Clean output  │    │ • Project rules  │    │ • Generated     │
│ • Only result   │    │ • Security focus │    │   prompts       │
│ • User-friendly │    │ • Type safety    │    │ • Ready for AI  │
└─────────────────┘    └──────────────────┘    └─────────────────┘

### Pattern 4: Direct Q&A with File Context (NEW - ask_gemini)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Development Q&A │───▶│ ask_gemini       │───▶│ Instant Answer  │
│ • "How do I fix │    │ • user_          │    │ • Direct response│
│   this error?"  │    │   instructions   │    │ • Code examples │
│ • Files: error.│    │ • file_selections│    │ • Explanations  │
│   py:45-90      │    │ • In-memory gen  │    │ • No files saved│
└─────────────────┘    │ • Single call    │    └─────────────────┘
                       │ • Direct to AI   │
                       └──────────────────┘
```

### Pattern 2: Context Generation for Inspection

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Need Context    │───▶│ generate_code_   │───▶│ Context File    │
│ File            │    │ review_context   │    │ • Enhanced      │
│ • Debug/inspect │    │ • text_output=   │    │ • Meta prompts  │
│ • Understand    │    │   false          │    │ • Git analysis  │
│ • Custom review │    │ • File creation  │    │ • Config data   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Pattern 5: MCP PR Review Flexibility (Parameter Control)

```
CLEAN DEFAULT WORKFLOW        CONTEXT INSPECTION MODE       CONTENT RETURN MODE
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│ generate_pr_    │────────▶│ generate_pr_     │────────▶│ generate_pr_    │
│ review()        │         │ review(          │         │ review(         │
│ • DEFAULT       │         │   create_context │         │   text_output=  │
│ • In-memory     │         │   _file=true     │         │   true          │
│ • Clean output  │         │ )                │         │ )               │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                            │                            │
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│ Result:         │         │ Result:          │         │ Result:         │
│ • Only AI       │         │ • Context file   │         │ • Direct AI     │
│   review file   │         │ • No AI review   │         │   content       │
│ • pr-review-    │         │ • code-review-   │         │ • No files      │
│   feedback-*.md │         │   context-*.md   │         │ • Text response │
│ • Success msg   │         │ • Success msg    │         │ • AI chaining   │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

### Pattern 6: Traditional Context → AI Review (Backwards Compatible)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Context Gen     │───▶│ generate_code_   │───▶│ Context File    │
│ • Task lists    │    │ review_context   │    │ • Git diffs     │
│ • Git analysis  │    │ • auto_meta_     │    │ • Task progress │
│ • Config files  │    │   prompt=false   │    │ • Config files  │
│ • Legacy mode   │    │ • text_output:   │    │ • Basic prompt  │
│                 │    │   false          │    │ • File output   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ AI Review File  │◀───│ AI Review        │◀───│ Context File    │
│ • Final output  │    │ • context_file   │    │ • Traditional   │
│ • Comprehensive │    │   mode           │    │ • Review ready  │
│ • AI feedback   │    │ • Standard       │    │ • Structured    │
│ • File paths    │    │   processing     │    │ • Compatible    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎛️ Configuration Flow

### Configuration Discovery Process (Updated with Import Resolution)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Project Scan    │───▶│ CLAUDE.md        │───▶│ Import Resolution│
│ • Start at root │    │ Discovery        │    │ • @import syntax│
│ • Recursive     │    │ • Project level  │    │ • Max 5 hops    │
│ • Async ops     │    │ • User level     │    │ • Circular check│
│ • Check flags   │    │ • Enterprise     │    │ • Path resolve  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Cursor Rules     │◀───│ Import Merge    │
                       │ Discovery        │    │ • Deduplicate   │
                       │ • .cursorrules   │    │ • Combine files │
                       │ • .cursor/rules  │    │ • Keep hierarchy│
                       │ • Monorepo scan  │    │ • Error collect │
                       └──────────────────┘    └─────────────────┘
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Configuration    │───▶│ Template Engine │
                       │ Merger & Cache   │    │ • Apply configs │
                       │ • Deduplication  │    │ • Insert rules  │
                       │ • Hierarchy      │    │ • Format output │
                       │ • Validation     │    │ • Context ready │
                       │ • Cache results  │    │ • Performance   │
                       └──────────────────┘    └─────────────────┘
```

**Key Implementation Details Not Shown Above:**
- **Async/Concurrent Operations**: `async_configuration_discovery.py` provides performance optimization
- **Caching Mechanism**: `ConfigurationCache` in `context_builder.py` prevents redundant operations
- **Error Collection**: Comprehensive error tracking throughout pipeline
- **Performance Stats**: Timing and metrics collection for optimization

## 📊 Data Flow Summary (Updated Architecture)

### Input Sources → Enhanced Processing → Output Formats

```
INPUT SOURCES                ENHANCED PROCESSING            OUTPUT FORMATS
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│ • Context files │────────▶│ Auto Meta Prompt │────────▶│ • .md files     │
│ • Project paths │         │ • Optimized gen  │         │ • Clean text    │
│ • Direct content│         │ • No temp files  │         │ • MCP responses │
│ • Git branches  │         │ • Config discovery│        │ • Raw prompts   │
│ • GitHub PRs    │         │ • Git operations │         │ • AI feedback   │
│ • Task lists    │         │ • AI processing  │         │ • File paths    │
│ • File selections│        │ • Token limits   │         │ • Temp cleanup  │
│   with ranges   │         │ • Clean responses│         │ • Token reports │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        ▲                            ▲                            ▲
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│ Configuration   │────────▶│ Smart Defaults   │────────▶│ Enhanced Output │
│ • CLAUDE.md     │         │ • auto_meta_     │         │ • CLI commands  │
│ • Cursor rules  │         │   prompt=true    │         │ • MCP tools     │
│ • Templates     │         │ • Scope detection│         │ • AI chaining   │
│ • Model config  │         │ • Multi-mode     │         │ • Embed prompts │
│ • Meta prompts  │         │ • Error handling │         │ • Project-aware │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

### Processing Modes (Enhanced)

```
IN-MEMORY MODE (DEFAULT)      ENHANCED MODE                 TRADITIONAL MODE
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│ PR Review       │────────▶│ Auto Meta        │────────▶│ Legacy Support  │
│ In-Memory       │         │ Prompt           │         │ • auto_meta_    │
│ • create_context│         │ • auto_meta_     │         │   prompt=false  │
│   _file=false   │         │   prompt=true    │         │ • Traditional   │
│ • text_output=  │         │ • Project-aware  │         │   workflow      │
│   false         │         │ • Optimized      │         │ • Basic prompts │
│ • Clean results │         │ • File creation  │         │ • File creation │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        ▼                            ▼                            ▼
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│ Memory-Only     │         │ Enhanced         │         │ Standard        │
│ Processing      │         │ Context          │         │ Context         │
│ • No temp files │         │ • Meta prompts   │         │ • Basic templates│
│ • Direct AI     │         │ • Config rules   │         │ • Standard format│
│ • Single output │         │ • Type safety    │         │ • Compatible    │
│ • User-friendly │         │ • Security       │         │ • Legacy support│
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

### File Generation Patterns

```
DEFAULT PATTERN (NEW)         INSPECTION PATTERN           NO-FILE PATTERN
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│ PR Review       │────────▶│ Context Creation │────────▶│ AI Agent Chain  │
│ In-Memory       │         │ • create_context │         │ • text_output:  │
│ • Only AI       │         │   _file=true     │         │   true          │
│   review file   │         │ • Context file   │         │ • Direct return │
│ • Clean result  │         │ • Debug/inspect  │         │ • No artifacts  │
│ • User-friendly │         │ • Traditional    │         │ • Memory only   │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

---

## 🔧 Tool Dependencies

### CLI Commands Dependencies
- `gemini-code-review-mcp` → `src.server:main` (MCP server)
- `generate-code-review` → `src.cli_main:main`
- `generate-meta-prompt` → `src.meta_prompt_generator:main`
- `generate-file-context` → `src.cli_generate_file_context:main` (for debugging, no AI)
- `ask-gemini` → `src.ask_gemini_cli:main`
- `ask-gemini-direct` → `src.ask_gemini_cli:direct_main`

### MCP Tools Dependencies
**Available MCP Tools (as of v0.4.2):**
- `generate_ai_code_review` - Complete AI code review
- `generate_pr_review` - GitHub PR analysis
- `ask_gemini` - Generate context and get AI response
- `generate_file_context` (Deprecated) - Generate context without AI

**Internal Helpers (not exposed as MCP tools):**
- `generate_code_review_context` - Build review context
- `generate_meta_prompt` - Create contextual prompts

- All MCP tools → `src.server.py` → Individual modules
- Configuration discovery → `src.configuration_context.py`
- GitHub PR analysis → `src.github_pr_integration.py`
- File-based context → `src.file_context_generator.py`, `src.file_selector.py`
- AI processing → Google Gemini API

### External Service Dependencies
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Google Gemini   │───▶│ AI Processing    │───▶│ Review Output   │
│ API             │    │ • Text generation│    │ • Feedback      │
│ • GEMINI_API_KEY│    │ • Model selection│    │ • Analysis      │
└─────────────────┘    │ • Temperature    │    │ • Suggestions   │
                       └──────────────────┘    └─────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ GitHub API      │───▶│ PR Processing    │───▶│ PR Context      │
│ • GITHUB_TOKEN  │    │ • Fetch PR data  │    │ • Diff analysis │
│ • Repository    │    │ • Extract changes│    │ • Metadata      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🧪 Testing Workflow

### Running Tests (See CLAUDE.md for Official Method)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Development     │───▶│ Virtual Env      │───▶│ Test Execution  │
│ • Clone repo    │    │ • python3 -m venv│    │ • python -m     │
│ • Make changes  │    │ • source venv/   │    │   pytest tests/ │
│ • Write tests   │    │   bin/activate   │    │ • Specific files│
│ • TDD approach  │    │ • pip install -e │    │ • Verbose mode  │
└─────────────────┘    │   ".[dev]"       │    │ • Type checking │
                       └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Test Results    │◀───│ Test Runner      │◀───│ Test Discovery  │
│ • Pass/Fail     │    │ • pytest engine  │    │ • test_*.py     │
│ • Coverage      │    │ • Mock external  │    │ • Test* classes │
│ • Type errors   │    │ • Async support  │    │ • test_* funcs  │
│ • Performance   │    │ • Fixtures       │    │ • conftest.py   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Key Testing Principles:**
- Always use virtual environment for isolation
- Install with `-e` for editable development
- Use `python -m pytest` for consistent module resolution
- Mock all external services (Gemini API, GitHub API)
- Follow TDD: Write tests first, then implementation