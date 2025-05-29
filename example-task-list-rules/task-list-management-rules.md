# Task List Management

Guidelines for managing task lists in markdown files to track progress on completing a PRD

## Task Implementation

- **One sub-task at a time**
- Continuously iterate until you have made the most detailed and impressive version you can for each task.

- **While working on a sub-task, if you encounter an error or bug**:
  FOLLOW THE DEBUGGING PROTOCOL: When debugging, investigate and fix autonomously but maintain laser focus on the specific issue. Only restore intended behavior - never add features, refactor, or implement alternatives beyond what was explicitly requested. If broader improvements are needed, you may note them but stick to minimal fixes that address the exact malfunction.

Only fix the exact problem identified. If the root cause suggests broader changes are needed, note this but stick to minimal fixes that address the specific issue.

- **Completion protocol:**
  1. When you finish a **sub‑task**, conduct a quick code review and make any necessary corrections.
  2. After making any necessary corrections, immediately mark that sub-task as completed by changing `[ ]` to `[x]`.
  3. If **all** subtasks underneath a parent task are now `[x]`, also mark the **parent task** as completed.

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
   - Mark the **parent task** `[x]` once **all** its subtasks are `[x]`.
3. Add newly discovered tasks.
4. Keep “Relevant Files” accurate and up to date.
5. Before starting work, check which sub‑task is next.
6. After implementing a sub‑task, conduct a quick code review and make any necessary corrections.
7. After implementing a sub‑task and finishing the code review, update the file and then continue on to the next sub‑task.
8. After completing everything in the current phase, please remember to delete the temporary files created during the process that weren't explicitly part of the subtasks