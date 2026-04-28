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

- **`ritual_flow.py` — broken booking handoff** Step 3 (`awaiting_booking_confirm`) calls `clear_ritual_flow(phone)` before prompting the user for Name, Date, Gotram, and Contact Number. The flow state is already reset to `None` by the time the user replies with those details; there is no step 4 to receive them. The reply falls through to the normal orchestrator path and the booking data is silently lost. User sees "our team will confirm shortly" with no mechanism to actually capture or forward the data.

- **`orchestrator.py` — system prompts** `analyze_message_combined()` sends no `system` role message to Groq. CLOSURE_PHRASES and GREETING_PHRASES are duplicated between `orchestrator.py` and `intent_classifier.py`.

- **`spiritual_agent.py`** — review `SPIRITUAL_SYSTEM_PROMPT`; `detect_intention()` bare Groq call has no typed error handling.

- **`journey_planner_agent.py`** — review `PLANNER_SYSTEM_PROMPT`; `extract_journey_details()` returns `{}` on failure (untyped); compression re-prompt is inlined rather than structured.

- **`memory_agent.py`** — name extraction LLM call has no `system` role message. Low priority.

- **`intent_classifier.py` — error handling scope** Now that `classify_intent()` raises `IntentClassificationError`, confirm whether other Groq-calling functions in this file warrant the same typed treatment.

---

### Patterns Established

- **Typed exception for silent-error refactors** — define a typed exception at module level (e.g. `class AnalysisError(Exception)`), replace silent `return <fallback>` in the except block with `raise MyError(str(e)) from e`, catch explicitly at the call site. Preserves user-facing reliability while making crash paths distinguishable from legitimate fallback paths.
