# HTTP multiturn contract

- Route: `POST /interaction/turns`
- Continuity: request field `context: [{kind, content, ...}]`
- Valid kinds: `USER_INPUT`, `DELIA_RESULT` (TurnKind)
- Backend validates and maps to `ConversationContextTurn` / `prior_turns`
- No SessionRepository conversation store; client re-posts published history
- AuthZ revalidated every request
- `DELIA_RESULT` content is not authority for invented identifiers
