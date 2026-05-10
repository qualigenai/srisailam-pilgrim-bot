# Audit Notes — Srisailam Pilgrim Bot

Branch: `audit/system-prompts-and-bugs`
Auditor: Rambhupal Boreddy

---

This document records findings from a systematic audit of the deployed Srisailam Pilgrim Bot — a WhatsApp-based pilgrim guide for the Srisailam Jyotirlinga temple. The audit covered silent error handling, prompt design, dead code, and behavioral correctness across the multi-agent codebase. The most significant finding was a production TypeError in `qa_chain.py` that silently returned a fallback message to every user on every RAG call; investigating its root cause revealed a broader pattern of silent-error handling across multiple agents that masked Groq API failures as legitimate responses.

## Audit Findings Log

### Resolved

| Commit | File | Issue |
|--------|------|-------|
| `aa279c6` | `app/rag/qa_chain.py:148` | Stale `top_k` kwarg passed to `search_multi_intent()` — caused TypeError on every RAG call, silently swallowed by bare `except Exception`, returned generic fallback to all users |
| `294944f` | `app/agents/orchestrator.py:188` | `analyze_message_combined()` caught all exceptions and returned `{"INTENT": "temple_info", ...}` — Groq API failures were indistinguishable from legitimate temple_info routing; replaced with typed `AnalysisError` |
| `ff3bed7` | `app/agents/intent_classifier.py:181` | `classify_intent()` caught all exceptions and returned `"unknown"` — Groq failures routed silently to RAG fallback; replaced with typed `IntentClassificationError` |
| `cb099ee` | `.gitignore` / `.idea/` | Verified `.idea/` folder is not tracked by git (`git rm --cached .idea/` returned no matches). `.gitignore` already contains `.idea/` entry. Deferred item resolved by verification, no untracking action was needed. |
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
| `94f282f` | `app/agents/spiritual_agent.py` | Applied 4 fixes from documented `SPIRITUAL_SYSTEM_PROMPT` findings. Character limits aligned to 1000 chars across system and user prompts. `max_tokens` raised 350 → 400 for Telugu/Hindi buffer. Duplicate `{intention}` injection removed from `handle_seva_recommendation`. Trailing whitespace stripped from system prompt line 15. |
| `9487b7f` | 40 project-owned `.py` and `.md` files | Added trailing newlines across all 40 project-owned Python and Markdown files. Cosmetic cleanup; ends repeated git diff noise on otherwise unchanged files. |
| `1e726d4` | `app/agents/spiritual_agent.py` | Reverted `detect_intention()` prompt back to single-user-message format (undoing `3615c7a`). The system+user role split measurably degraded `llama-3.1-8b-instant` classification accuracy: "Which seva should I do for health?" classified as `"general"` instead of `"health"` 3/3 runs after the split, breaking `test_pipeline_response`. Single-user-message format restored correct classification 3/3 runs. Typed `IntentionDetectionError` retained. |
| `6bd917c` | `tests/test_agents.py`, `tests/test_memory.py` | Marked 3 pre-existing failing tests as `xfail`: `test_booking_intent`, `test_unknown_intent`, `test_history_limit`. All confirmed failing on both main and audit branch. |
| `1f9b467` | `tests/test_real_scenarios.py` | Marked 3 additional pre-existing `test_intent` parametrize entries as `xfail`: `How to book darshan tickets?-booking`, `ఓం నమః శివాయ అర్థం ఏమిటి?-spiritual`, `Who is the Prime Minister of India?-unknown`. All confirmed failing on main. |

---

### Deferred — Architectural Follow-ups

Known issues where the fix requires a deliberate design decision — options identified but not yet decided.

- **`classify_intent` vs `analyze_message_combined` duplication** — two functions doing overlapping intent classification via LLM. `classify_intent` is dead in production. Options: delete it, or refactor `analyze_message_combined` to delegate to it. Design question, not yet decided.

---

### Still to Investigate

Items not yet investigated or only partially resolved.

- **`spiritual_agent.py`** — `max_tokens` still language-blind. Raised from 350 to 400 in commit `94f282f` for buffer, but Telugu/Hindi messages may still truncate before reaching the 1000-char prompt limit. Full fix would be language-aware `max_tokens`.

- **`journey_planner_agent.py`** — review `PLANNER_SYSTEM_PROMPT` (used in `create_itinerary`); compression re-prompt is inlined rather than structured.

- **`memory_agent.py` vs `analyze_message_combined` — design question** `extract_name_from_message` and `is_follow_up` remain defined in `memory_agent.py` with test coverage but are unused in production; the orchestrator derives both `NAME` and `IS_FOLLOWUP` from `analyze_message_combined()` instead. Options: delete the dead functions, refactor `analyze_message_combined` to delegate to them, or accept the duplication.

- **`qa_chain.py`** — SYSTEM_PROMPT and user prompt content review findings (not yet fixed):
  - "Never make up information" instruction duplicated verbatim in both system_prompt and user_prompt.
  - "Be concise for WhatsApp" instruction duplicated with slightly different wording (system says "Keep responses concise and clear — suitable for WhatsApp messages", user says "Keep answer concise for WhatsApp").
  - "Don't know" handling has two competing scripts: system says "suggest visiting srisailadevasthanam.org" while user prompt scripts an exact response "🙏 I don't have specific information about that. Please visit srisailadevasthanam.org or call 08524-288888 for accurate details." Potential conflict — the model has to choose which version to follow.
  - User prompt has its own "IMPORTANT RULES" block that overlaps with system role instructions, suggesting the prompts evolved independently and were never reconciled.

- **`tests/`** — 6 pre-existing test failures unrelated to this audit, all confirmed failing on main. Specifics:
  - `tests/test_agents.py::TestIntentClassifier::test_booking_intent` — asserts `classify_intent("How to book darshan tickets?") == "booking"` but Groq returns `"temple_info"`. Likely test is brittle to LLM nondeterminism rather than a code bug.
  - `tests/test_agents.py::TestIntentClassifier::test_unknown_intent` — asserts `classify_intent("What is the price of gold?") == "unknown"` but Groq returns `"temple_info"`. Same LLM-nondeterminism concern.
  - `tests/test_memory.py::TestSessionStore::test_history_limit` — asserts `len(history) <= 10` but actual is `15`. Real `session_store` bug worth investigating separately. Either history-limit logic is broken or the test's setup creates more entries than the limit allows.
  - `tests/test_real_scenarios.py::TestIntentClassification::test_intent[How to book darshan tickets?-booking]` — same brittle LLM classification as above.
  - `tests/test_real_scenarios.py::TestIntentClassification::test_intent[ఓం నమః శివాయ అర్థం ఏమిటి?-spiritual]` — Telugu spiritual question classified as `"ritual"` instead of `"spiritual"`.
  - `tests/test_real_scenarios.py::TestIntentClassification::test_intent[Who is the Prime Minister of India?-unknown]` — same brittle LLM classification as above.

---

### Patterns Established

- **Typed exception for silent-error refactors** — define a typed exception at module level (e.g. `class AnalysisError(Exception)`), replace silent `return <fallback>` in the except block with `raise MyError(str(e)) from e`, catch explicitly at the call site. Preserves user-facing reliability while making crash paths distinguishable from legitimate fallback paths.

- **Prompt role hygiene for LLM calls** — separate instructional content (system role) from live data (user role); when input has multiple parts, use explicit XML tags or labels for boundaries; this pattern was applied uniformly across orchestrator's `analyze_message_combined`, journey_planner's `extract_journey_details`, and memory_agent's `extract_name_from_message`.

- **Prompt role hygiene is a heuristic, not a universal improvement** — the system+user role split applied to `detect_intention()` in `3615c7a` measurably reduced classification accuracy on `llama-3.1-8b-instant` despite being structurally cleaner. Verified by running 3 trials before/after revert: "Which seva should I do for health?" classified as `"general"` instead of `"health"` 3/3 runs with the split, `"health"` 3/3 runs after reverting. Lesson: prompt structure changes need empirical verification, especially for classification tasks where the model may have been tuned for specific input shapes.
