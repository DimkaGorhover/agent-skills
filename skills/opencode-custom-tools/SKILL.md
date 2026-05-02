---
name: opencode-custom-tools
description: Use when creating, discovering, or debugging OpenCode custom tools in `.opencode/tools/` or `~/.config/opencode/tools/` — file naming, default vs named exports, Zod args, context fields, built-in name collisions, or delegating to Python or Bash from a tool definition.
metadata:
  author: d.horkhover
  version: 1.1.0
---

# OpenCode Custom Tools

## Overview

Custom tools are TypeScript or JavaScript files in `.opencode/tools/` or `~/.config/opencode/tools/` that OpenCode loads automatically so the LLM can call them during conversations. They can work alongside built-in tools, override them by name, or delegate work to scripts in other languages.

## When to Use

- Creating a new tool the LLM can invoke (database queries, API calls, project-specific scripts)
- Debugging why a tool is not discovered or not executing correctly
- Naming multiple tools from one file (`<filename>_<exportname>` convention)
- Intentionally overriding a built-in tool (e.g., sandboxing `bash`)
- Invoking Python, Bash, or any other language from a TypeScript tool wrapper
- Accessing session context (`directory`, `worktree`, `sessionID`, `agent`, `messageID`) inside a tool

## When NOT to Use

- MCP servers — those are configured differently (see OpenCode MCP docs)
- Built-in tool permissions/disabling — use the `permissions` config, not a custom tool
- Project-specific shell scripts that don't need LLM access — no need to wrap them as tools

## Quick Reference

| Concept                 | Detail                                                                            |
| ----------------------- | --------------------------------------------------------------------------------- |
| Local tool dir          | `.opencode/tools/` (project-level)                                                |
| Global tool dir         | `~/.config/opencode/tools/`                                                       |
| Discovery               | No registration step — files are loaded from the tool directories automatically   |
| Supported file types    | `.ts`, `.js`                                                                      |
| Tool name               | filename (without extension) for default export                                   |
| Multi-tool name         | `<filename>_<exportname>` for named exports                                       |
| Built-in override       | Custom tool with same name takes precedence over built-in                         |
| Schema library          | `tool.schema` (Zod alias) or `import { z } from "zod"`                            |
| Plain object form       | Export a plain object with `args` built from `zod` (no `tool()` wrapper required) |
| Context fields          | `agent`, `sessionID`, `messageID`, `directory`, `worktree`                        |
| Runtime for shell calls | `Bun.$` template literal                                                          |

## Core Pattern

### Single tool (default export with `tool()` helper)

```typescript
// .opencode/tools/database.ts  →  tool name: "database"
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Query the project database",
  args: {
    query: tool.schema.string().describe("SQL query to execute"),
  },
  async execute(args) {
    // implementation
    return `Executed: ${args.query}`
  },
})
```

### Plain object export (direct Zod — no `tool()` wrapper)

```typescript
// .opencode/tools/echo.ts
import { z } from "zod"

export default {
  description: "Echo a string",
  args: {
    value: z.string().describe("Text to echo"),
  },
  async execute(args: { value: string }) {
    return args.value
  },
}
```

### Multiple tools from one file

```typescript
// .opencode/tools/math.ts  →  tools: "math_add", "math_multiply"
import { tool } from "@opencode-ai/plugin"

export const add = tool({
  description: "Add two numbers",
  args: {
    a: tool.schema.number().describe("First number"),
    b: tool.schema.number().describe("Second number"),
  },
  async execute(args) {
    return args.a + args.b
  },
})

export const multiply = tool({
  description: "Multiply two numbers",
  args: {
    a: tool.schema.number().describe("First number"),
    b: tool.schema.number().describe("Second number"),
  },
  async execute(args) {
    return args.a * args.b
  },
})
```

### Using session context

```typescript
// .opencode/tools/project.ts
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Get project information",
  args: {},
  async execute(args, context) {
    const { agent, sessionID, messageID, directory, worktree } = context
    // directory = session working directory
    // worktree  = git worktree root
    return `Agent: ${agent}, Session: ${sessionID}, Dir: ${directory}`
  },
})
```

### Delegating to an external script (Python example)

```typescript
// .opencode/tools/python-add.ts
import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Add two numbers using Python",
  args: {
    a: tool.schema.number().describe("First number"),
    b: tool.schema.number().describe("Second number"),
  },
  async execute(args, context) {
    // context.worktree gives the repo root — use it for absolute script paths
    const script = path.join(context.worktree, ".opencode/tools/add.py")
    const result = await Bun.$`python3 ${script} ${args.a} ${args.b}`.text()
    return result.trim()
  },
})
```

```python
# .opencode/tools/add.py
import sys

a = int(sys.argv[1])
b = int(sys.argv[2])
print(a + b)
```

### Replacing a built-in tool

```typescript
// .opencode/tools/bash.ts  — overrides built-in "bash" tool
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Restricted bash — blocks all commands",
  args: {
    command: tool.schema.string(),
  },
  async execute(args) {
    return `blocked: ${args.command}`
  },
})
```

> ⚠️ To _disable_ a built-in without replacing it, use the `permissions` config instead.

## Common Mistakes

| Mistake                                   | Fix                                                                                                              |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Tool not discovered                       | Put the file in `.opencode/tools/` or `~/.config/opencode/tools/` with a `.ts`/`.js` extension                   |
| Expecting a registration step             | Tools are auto-discovered from the tool directories — no separate registration needed                            |
| Unexpected built-in override              | A custom tool with the same name takes precedence over a built-in — rename it unless intentional                 |
| Named exports not matching expectations   | Each named export becomes `<filename>_<exportname>` — confirm the filename and export name                       |
| Plain object export without correct shape | When using direct `zod` (no `tool()` wrapper), follow the plain-object pattern: `{ description, args, execute }` |
| Shell output includes trailing newline    | Use `.trim()` before returning shell output                                                                      |
