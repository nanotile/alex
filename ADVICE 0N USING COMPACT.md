Great question, Kent. Here's the rundown on what compaction does and the tradeoffs involved.

## What Happens When Claude Code Compacts

When your conversation approaches the context window limit, Claude Code automatically analyzes the conversation to identify key information worth preserving, creates a concise summary of previous interactions, decisions, and code changes, then replaces old messages with that summary. The goal is to let you keep working without a hard cutoff.

**The good:** Unlike clearing the context completely, compacting preserves essential nuances and key information, allowing you to pick up where you left off. It also reduces token usage and helps Claude stay on track during long sessions.

**The bad:** There's real information loss. Developers have noted that responses can become generic after compaction, previous decisions get forgotten, and code quality noticeably degrades — especially when compaction triggers late in a session when context is already "poisoned."

## Compact vs. New Conversation — When to Do What

The consensus from experienced users breaks down like this:

**Manual `/compact` at logical breakpoints is the best strategy.** Run `/compact` with custom instructions like `/compact Focus on the API changes` to control what gets preserved. You can also customize compaction behavior in your CLAUDE.md to ensure critical context survives summarization.

**Start a new conversation when:**
- You're switching to a fundamentally different task or area of the codebase
- If you're switching from brainstorming to analyzing something different, start a new chat — don't bleed contexts. This keeps the AI's "whiteboard" clean and focused on only the relevant information.
- The session has already compacted multiple times and quality is slipping

**Use subagents for research-heavy work.** Subagents run in separate context windows and report back summaries, keeping your main conversation clean for implementation. Since context is your fundamental constraint, subagents are one of the most powerful tools available.

## Practical Tips for Your Workflow

1. **Compact proactively** — don't wait for auto-compact. The real strategy is to manually compact at strategic times rather than letting auto-compact happen randomly.
2. **Disable unused MCP servers** — run `/mcp` to free up context space before it becomes an issue.
3. **Put persistent project info in CLAUDE.md** — Use a dedicated context file to inject fundamental requirements every session. This is where core app features, tech stacks, and "never-forgotten" project notes live, moving stable information out of the limited conversation window.
4. For your multi-Lambda "alex" project work, breaking tasks into separate sessions per agent component would probably give you better results than running a marathon session with repeated compactions.

**Bottom line:** Compaction is useful but lossy. A fresh conversation with a well-crafted initial prompt (or a good CLAUDE.md) will generally outperform a session that's been compacted several times. Use `/compact` tactically at task boundaries, and start fresh when switching contexts.