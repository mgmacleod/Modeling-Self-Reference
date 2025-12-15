# LLM Context Management Guide

**Document Type**: Reference  
**Target Audience**: Human developers working with LLM assistants  
**Purpose**: Explain non-intuitive aspects of LLM context windows and how they affect this project  
**Last Updated**: 2025-12-15  
**Status**: Active

---

## The Context Window Problem

LLMs have finite context windows (~100k-200k tokens depending on model). In long sessions, early messages get truncated or compressed.

**What this means for this project**:
- Documentation loaded at session start may be lost by session end
- Instructions given early in conversation won't persist
- Files read via tools become "conversation history" and can be displaced

---

## How VS Code Copilot Handles Context

### What Persists Across Turns

1. **System prompts** (configured in VS Code settings)
   - Injected fresh every turn
   - Not part of conversation history
   - Small token budget (~200-500 tokens max recommended)

2. **Active file in editor**
   - Re-loaded automatically each turn
   - Full file contents injected
   - **Important**: This uses tokens even if you're not discussing the file!

3. **Paperclip attachments** (folders/files)
   - Persist across conversation
   - Folder attachments give structure, not full contents
   - File attachments give full contents

### What Gets Truncated

1. **File reads via tools** (`read_file`)
   - Stored as conversation history
   - Subject to truncation in long sessions

2. **Early conversation messages**
   - Compressed or dropped as context fills
   - Instructions from turn 1 may not reach turn 100

3. **Tool outputs**
   - Command outputs, search results, etc.
   - Treated as conversation history

---

## Best Practices for This Project

### Starting a Session

1. **Paperclip attach**: `llm-facing-documentation/` folder
   - Gives LLM the directory structure
   - Low token cost
   
2. **Let LLM read Tier 1 docs**:
   - project-timeline.md (latest entries)
   - documentation-standards.md
   - project-management-practices.md

3. **Close unnecessary files** in editor
   - Active file = automatic context injection every turn
   - Only keep files open that you're actively working on

### During Long Sessions

1. **Monitor what file is active**
   - Large files open = large token cost per turn
   - Switch to small/empty file when discussing non-code topics

2. **Re-attach critical docs before major operations**
   - End-of-session: Re-attach management practices
   - Theory work: Re-attach relevant theory docs

3. **Don't rely on early-session instructions**
   - Use system prompts for critical behaviors
   - Re-state important constraints when needed

### Token Budget Awareness

**Typical session**:
- System prompts: ~200 tokens/turn (persistent)
- Active file: 0-10k tokens/turn (automatic)
- Conversation history: 20-50k tokens (cumulative, truncates)
- Paperclip attachments: 1-5k tokens (persistent)

**Rule of thumb**: If a file is >5k tokens and not directly relevant, close it.

---

## The Displacement Effect

**Example scenario**:
1. Session starts, load 20k tokens of documentation
2. Work for 50 turns, reading code, running commands
3. Total conversation: 80k tokens
4. Early documentation reads get compressed to ~2k tokens
5. **Detail is lost**

**Solution**: Re-inject critical documentation when needed, don't assume it's still in full context.

---

## Why This Matters for Reproducibility

Different context management strategies = Different information available to LLM = Different behavior.

Two researchers working on this project:
- **Researcher A**: Keeps large theory docs open, re-reads files frequently
- **Researcher B**: Closes files, relies on conversation history

→ LLM may behave differently due to different available context

**Standardized practice**: Follow the bootstrap protocol in project documentation for consistent results.

---

## Technical Details (For Deep Understanding)

### Context Window Structure (Approximate)

```
[System Prompt] (200 tokens, persistent)
[Active File] (variable, re-injected each turn)
[Paperclip Attachments] (variable, persistent)
[Conversation Turn 1] (truncated in long sessions)
[Conversation Turn 2] (truncated in long sessions)
...
[Conversation Turn N-10] (recent, full detail)
[Conversation Turn N] (current, full detail)
```

### Truncation Strategy

LLMs typically use:
- **Summarization**: Early turns compressed to key points
- **Dropping**: Very old turns removed entirely
- **Recency bias**: Last ~10-20 turns preserved in full

This is why system prompts (re-injected) are more reliable than early conversation instructions.

---

## Future Considerations

As this project develops tools for automated context management, this guide will be updated with:
- Automated tier loading scripts
- Context budget monitoring tools
- Optimal document chunking strategies

---
