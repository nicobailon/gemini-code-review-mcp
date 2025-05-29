# Task List Management

Guidelines for managing task lists in markdown files to track progress on completing a PRD

## Task Implementation
- **One sub-task at a time:** Do **NOT** start the next sub‑task until you ask the user for permission and they say “yes” or "y"
- **Completion protocol:**  
  1. When you finish a **sub‑task**, immediately mark it as completed by changing `[ ]` to `[x]`.  
  2. If **all** subtasks underneath a parent task are now `[x]`, also mark the **parent task** as completed.  
- After each sub‑task proceed to the next sub-task within the same parent task.
- Once **all** its subtasks are `[x]` within a parent task, you need to run the `generate_code_review_context` tool to generate the code review context for that phase.

## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Add new tasks as they emerge.

2. **Maintain the “Relevant Files” section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## AI Instructions

When working with task lists, the AI must:

1. Regularly update the task list file after finishing any significant work.
2. Follow the completion protocol:
   - Mark each finished **sub‑task** `[x]`.
   - Once **all** its subtasks are `[x]` within a parent task, you need to run the `generate_code_review_context` tool to generate the code review context for that phase.
   - Once the context file is generated, use the `send_code_review_context` tool to send the markdown file to Gemini to code review. It will return the path to the review file.
   - Access the review file and add the code review feedback.
   - Mark the **parent task** `[x]` once the code review feedback is complete.
3. Add newly discovered tasks.
4. Keep “Relevant Files” accurate and up to date.
5. Before starting work, check which sub‑task is next.
6. After implementing a sub‑task, update the file and then pause for user approval.