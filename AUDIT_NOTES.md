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

---

### Deferred — Architectural Follow-ups

Known issues not yet acted on. Each requires a deliberate decision before touching.

- **`orchestrator.py:2` — dead import** `classify_intent` is imported but never called; `analyze_message_combined()` is the active intent path. Separate cleanup commit.

- **`classify_intent` vs `analyze_message_combined` duplication** — two functions doing overlapping intent classification via LLM. `classify_intent` is dead in production. Options: delete it, or refactor `analyze_message_combined` to delegate to it. Design question, not yet decided.

- **`awp_logger.py:54` — bare `except:`** Catches `json.JSONDecodeError` during audit log read, but bare `except` also catches `SystemExit`/`KeyboardInterrupt`. Should be `except (json.JSONDecodeError, ValueError)`.

- **`vectorstore.py:20` — bare `except:`** Silences the error when deleting a non-existent Chroma collection before rebuild. Intent is correct, but bare `except` is too broad. Should be `except Exception`.

- **Trailing newlines** — several files lack a trailing newline; git flags them on every diff. Cosmetic, low priority.

---

### Still to Investigate

- **`orchestrator.py` — duplicated phrase lists** CLOSURE_PHRASES and GREETING_PHRASES are duplicated between `orchestrator.py` and `intent_classifier.py`.

- **`spiritual_agent.py`** — review `SPIRITUAL_SYSTEM_PROMPT`.

- **`journey_planner_agent.py`** — review `PLANNER_SYSTEM_PROMPT` (used in `create_itinerary`); compression re-prompt is inlined rather than structured.

- **`memory_agent.py`** — three open issues:
  - `extract_name_from_message()` has no `system` role message (instruction text combined with user message in single user turn)
  - `extract_name_from_message()` silently returns `None` on exception (same pattern as other agents — needs typed exception)
  - 2 of 3 functions are dead code in production: `extract_name_from_message` and `is_follow_up` are imported in `orchestrator.py:15` but never called; the orchestrator derives both `NAME` and `IS_FOLLOWUP` from `analyze_message_combined()` instead. Design question: delete the dead functions, refactor `analyze_message_combined` to delegate to them, or accept the duplication.

- **`intent_classifier.py` — error handling scope** Now that `classify_intent()` raises `IntentClassificationError`, confirm whether other Groq-calling functions in this file warrant the same typed treatment.

---

### Patterns Established

- **Typed exception for silent-error refactors** — define a typed exception at module level (e.g. `class AnalysisError(Exception)`), replace silent `return <fallback>` in the except block with `raise MyError(str(e)) from e`, catch explicitly at the call site. Preserves user-facing reliability while making crash paths distinguishable from legitimate fallback paths.
