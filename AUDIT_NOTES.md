# Audit Notes — Srisailam Pilgrim Bot

Branch: `audit/system-prompts-and-bugs`
Auditor: Rambhupal Boreddy

---

## Audit Findings Log

### Resolved

| Commit | File | Issue |
|--------|------|-------|
| `aa279c6` | `app/rag/qa_chain.py:148` | Stale `top_k` kwarg passed to `search_multi_intent()` — caused TypeError on every RAG call, silently swallowed by bare `except Exception`, returned generic fallback to all users |
| `294944f` | `app/agents/orchestrator.py:188` | `analyze_message_combined()` caught all exceptions and returned `{"INTENT": "temple_info", ...}` — Groq API failures were indistinguishable from legitimate temple_info routing; replaced with typed `AnalysisError` |
| `ff3bed7` | `app/agents/intent_classifier.py:181` | `classify_intent()` caught all exceptions and returned `"unknown"` — Groq failures routed silently to RAG fallback; replaced with typed `IntentClassificationError` |
| (this commit) | `.gitignore` / `.idea/` | Verified `.idea/` folder is not tracked by git (`git rm --cached .idea/` returned no matches). `.gitignore` already contains `.idea/` entry. Deferred item resolved by verification, no untracking action was needed. |
| `42bf45f` | `app/agents/orchestrator.py:144` | `analyze_message_combined()` prompt split into `system` + `user` roles; current message bounded in `<current_message>` tags, history in `<conversation_history>` tags; NAME/IS_FOLLOWUP scoped explicitly to current message to prevent history leakage |
| `3615c7a` | `app/agents/spiritual_agent.py:78` | `detect_intention()` prompt split into `system` + `user` roles; instruction text moved to `system`, raw message is the entire `user` turn |
| `48ed3ea` | `app/agents/spiritual_agent.py:97` | `detect_intention()` silently returned `"general"` on exception; replaced with typed `IntentionDetectionError`; targeted `except IntentionDetectionError as e` with `logger.warning` added in `handle_seva_recommendation` before the blanket `except Exception` |
| `6403113` | `app/flows/ritual_flow.py:101` | Step 3 booking confirmation message replaced misleading "please share Name/Date/Gotram/Contact" text (which implied bot data capture) with honest direction to temple website and Mana Mitra phone for actual booking |
| `a78aa78` | `app/agents/journey_planner_agent.py:33` | `extract_journey_details()` prompt split into `system` + `user` roles; instruction text moved to system, raw message is the entire user turn |
| `5e5be31` | `app/agents/journey_planner_agent.py` | `extract_journey_details()` replaced silent `return {}` with typed `JourneyDetailsError`; targeted catches added in `create_itinerary` (returns info prompt) and `needs_more_info` (returns `True`), both with `logger.warning` before degrading |
| `e924d24` | `app/agents/journey_planner_agent.py` | `create_itinerary()` replaced silent hardcoded fallback return with typed `ItineraryGenerationError`; targeted catch added in orchestrator's `process_message` with `logger.warning` and audit log step before returning the user-facing fallback message |
| `06cbd76` | `app/agents/orchestrator.py` | Removed four dead imports: `classify_intent`, `extract_name_from_message`, `is_follow_up`, `get_unknown_message`. All four functions remain defined in their source modules with test coverage; only the unused imports in `orchestrator.py` were removed. |
| `6bfea76` | `app/utils/awp_logger.py`, `app/rag/vectorstore.py` | Narrowed two bare `except` blocks. `awp_logger.py:54` now catches `(json.JSONDecodeError, UnicodeDecodeError)` for JSON parse fallback. `vectorstore.py:20` now catches `Exception` with `logger.debug` for visibility, replacing silent `pass`. |
| `c44594e` | `app/agents/memory_agent.py` | `extract_name_from_message()` prompt split into `system` + `user` roles; instruction text moved to system, raw message is the entire user turn |
| `c5efea4` | `app/agents/memory_agent.py` | `extract_name_from_message()` replaced silent `return None` with typed `NameExtractionError`. No call site changes needed — no production callers; tests are unaffected. |
| `8e412e7` | `app/utils/phrase_lists.py`, `app/agents/orchestrator.py`, `app/agents/intent_classifier.py` | Extracted 8 phrase lists to shared `app/utils/phrase_lists.py` module. 6 of 8 lists had drifted; merged using intent_classifier's richer copy. Behavioral improvement: orchestrator's deterministic short-circuits now match phrases like `"ok bye"`, `"cab from"`, `"ugadi"`, `"before visiting"` that previously fell through to LLM. |

---

### Deferred — Architectural Follow-ups

Known issues not yet acted on. Each requires a deliberate decision before touching.

- **`classify_intent` vs `analyze_message_combined` duplication** — two functions doing overlapping intent classification via LLM. `classify_intent` is dead in production. Options: delete it, or refactor `analyze_message_combined` to delegate to it. Design question, not yet decided.

- **Trailing newlines** — several files lack a trailing newline; git flags them on every diff. Cosmetic, low priority.

---

### Still to Investigate

- **`spiritual_agent.py`** — `SPIRITUAL_SYSTEM_PROMPT` review findings (not yet fixed):
  - Three different character limits that don't agree: system prompt says "under 1200 characters", user prompts in `handle_seva_recommendation` and `handle_spiritual_query` both say "under 1000 characters", `max_tokens=350` enforces ~1400 chars in English (less in Telugu/Hindi). Pick one number, align all three.
  - `max_tokens=350` is language-blind. Works for English (~1400 chars) but may truncate Telugu/Hindi mid-response since those languages use more tokens per character.
  - In `handle_seva_recommendation` user prompt, `{intention}` is injected twice — once in the opening line `"Recommend the best seva for {intention} at Srisailam"` and once as a labelled field `"Prayer intention: {intention}"`. Redundant.
  - Trailing whitespace after `"guide"` on line 15 of the system prompt.

- **`journey_planner_agent.py`** — review `PLANNER_SYSTEM_PROMPT` (used in `create_itinerary`); compression re-prompt is inlined rather than structured.

- **`memory_agent.py` vs `analyze_message_combined` — design question** `extract_name_from_message` and `is_follow_up` remain defined in `memory_agent.py` with test coverage but are unused in production; the orchestrator derives both `NAME` and `IS_FOLLOWUP` from `analyze_message_combined()` instead. Options: delete the dead functions, refactor `analyze_message_combined` to delegate to them, or accept the duplication.

- **`intent_classifier.py` — error handling scope** Now that `classify_intent()` raises `IntentClassificationError`, confirm whether other Groq-calling functions in this file warrant the same typed treatment.

- **`qa_chain.py`** — SYSTEM_PROMPT and user prompt content review findings (not yet fixed):
  - "Never make up information" instruction duplicated verbatim in both system_prompt and user_prompt.
  - "Be concise for WhatsApp" instruction duplicated with slightly different wording (system says "Keep responses concise and clear — suitable for WhatsApp messages", user says "Keep answer concise for WhatsApp").
  - "Don't know" handling has two competing scripts: system says "suggest visiting srisailadevasthanam.org" while user prompt scripts an exact response "🙏 I don't have specific information about that. Please visit srisailadevasthanam.org or call 08524-288888 for accurate details." Potential conflict — the model has to choose which version to follow.
  - User prompt has its own "IMPORTANT RULES" block that overlaps with system role instructions, suggesting the prompts evolved independently and were never reconciled.

---

### Patterns Established

- **Typed exception for silent-error refactors** — define a typed exception at module level (e.g. `class AnalysisError(Exception)`), replace silent `return <fallback>` in the except block with `raise MyError(str(e)) from e`, catch explicitly at the call site. Preserves user-facing reliability while making crash paths distinguishable from legitimate fallback paths.
