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

---

### Deferred — Architectural Follow-ups

Known issues not yet acted on. Each requires a deliberate decision before touching.

- **`classify_intent` vs `analyze_message_combined` duplication** — two functions doing overlapping intent classification via LLM. `classify_intent` is dead in production. Options: delete it, or refactor `analyze_message_combined` to delegate to it. Design question, not yet decided.

- **Trailing newlines** — several files lack a trailing newline; git flags them on every diff. Cosmetic, low priority.

---

### Still to Investigate

- **`orchestrator.py` vs `intent_classifier.py` — phrase lists are not just duplicated, they have DRIFTED.** 7 lists duplicated total (`CLOSURE_PHRASES`, `GREETING_PHRASES`, `GREETING_SINGLE_WORDS`, `DIRECTIONS_PHRASES`, `FESTIVAL_PHRASES`, `ACCOMMODATION_PHRASES`, `PREPARATION_PHRASES`). 6 of 7 have drifted — `intent_classifier.py` is consistently the more comprehensive copy. `orchestrator.py` is running on stale, shorter versions, which means its deterministic short-circuits are missing detections that `intent_classifier` has (e.g. `"ok bye"`, `"what to wear"`, multilingual variants). Fix is not pure refactoring — extracting to a shared module requires deciding to use `intent_classifier`'s richer union, which is a behavioral change to orchestrator's routing. Needs deliberate design + verification.

- **`spiritual_agent.py`** — review `SPIRITUAL_SYSTEM_PROMPT`.

- **`journey_planner_agent.py`** — review `PLANNER_SYSTEM_PROMPT` (used in `create_itinerary`); compression re-prompt is inlined rather than structured.

- **`memory_agent.py` vs `analyze_message_combined` — design question** `extract_name_from_message` and `is_follow_up` remain defined in `memory_agent.py` with test coverage but are unused in production; the orchestrator derives both `NAME` and `IS_FOLLOWUP` from `analyze_message_combined()` instead. Options: delete the dead functions, refactor `analyze_message_combined` to delegate to them, or accept the duplication.

- **`intent_classifier.py` — error handling scope** Now that `classify_intent()` raises `IntentClassificationError`, confirm whether other Groq-calling functions in this file warrant the same typed treatment.

---

### Patterns Established

- **Typed exception for silent-error refactors** — define a typed exception at module level (e.g. `class AnalysisError(Exception)`), replace silent `return <fallback>` in the except block with `raise MyError(str(e)) from e`, catch explicitly at the call site. Preserves user-facing reliability while making crash paths distinguishable from legitimate fallback paths.
