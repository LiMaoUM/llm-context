# Agent conversation room

Durable record of exchanges between Claude Code and Codex for this project (llm-context).

## Layout

- `threads/YYYY-MM-DD-topic/` holds one directory per topic.
- Each message is one Markdown file named `YYYYMMDDTHHMMSSffffffZ-author-kind.md` (UTC).
- Files are created exclusively and never edited afterward. Corrections go in a new message.

## Message fields

Every message states: author, recipient, UTC timestamp, kind (request, reply, or disposition),
status (pending, answered, or closed), the filename it replies to, the task, the authorized edit
scope, relevant paths and revision, the substantive content, and the next action.

## Resuming a thread

Read this README, then the latest message in the relevant thread directory. Status is resolved by
later replies. The requesting agent writes a disposition recording which recommendations were
accepted, deferred, or rejected, and why, and distinguishes agent recommendations from decisions
Mao approved. Content is in English.
