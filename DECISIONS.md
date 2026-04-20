# Design Decisions: Junior AI Engineer Task

## 1. Architecture: Manual ReAct Loop
Instead of using pre-built agent frameworks (prohibited by constraints), I implemented a custom **ReAct (Reasoning + Acting)** loop from scratch.

- **Why:** To handle complex, multi-step requests like "find the 3 worst ROI campaigns and delete them," the assistant must think, act, observe results, and repeat before giving a final answer.
- **Implementation:** The loop iterates up to 5 turns, parsing `Thought`, `Action`, and `Observation` tags. The LLM sees tool results before deciding the next step.
- **Hallucination Prevention:** The response is truncated at the `Action:` line before yielding, physically preventing the LLM from fabricating its own `Observation`. The system injects the real tool result instead.
- **Loop Control:** The loop breaks immediately on `Final Answer:`, on an action line containing "none" (case-insensitive), or any response with neither — preventing infinite loops from ambiguous model outputs.

## 2. Tool Layer: Pydantic & Pandas
- **Pydantic for Structure:** `ExcelTools` uses a Pydantic `BaseModel` for declarative field definitions with defaults. This provides a clean class structure, though runtime type enforcement relies on pandas and Python's own duck typing rather than Pydantic validators.
- **Priority Loading:** `_load_data` checks `data_modified/` before `data_original/`, ensuring sequential edits persist across operations without overwriting the source data.
- **Atomic Saves:** Every write operation (add, update, delete) triggers an immediate `_save_data()` call. While slightly slower than batching, this ensures data integrity — if a multi-step request fails halfway, previous successful steps are preserved.
- **Data Cleaning on Load:** Currency columns (Price, Budget, Spent, Revenue, Amount) are stripped of `$` and `,` and cast to float on every load. Integer columns (Impressions, Clicks, Conversions, Bedrooms, Bathrooms, Footage, Year) are similarly cleaned. This ensures numeric comparisons always work regardless of how the Excel file was originally formatted.
- **Excel Formatting on Save:** `_save_data` uses `openpyxl` to reapply the original formatting — date columns as `MM/DD/YYYY`, currency with `$` signs, integers with comma separators, auto-fitted column widths, and a styled header row. This keeps the modified file visually identical to the original.
- **Backtick Sanitization:** `update_record` and `add_record` strip backticks from dictionary keys before applying changes, preventing the LLM from accidentally creating new columns named `` `Revenue Generated` `` instead of updating `Revenue Generated`.

## 3. Tool Design: Covering the Full Query Surface
Rather than a single generic query tool, I built a suite of specialized tools to cover cases pandas `query()` alone cannot handle:

- **`query_data`:** Handles standard row filtering with automatic backtick wrapping for spaced column names and quote normalization for curly/smart quotes.
- **`summarize_data`:** Groups data and returns mean, sum, max, min, and count in one call. Used for questions like "which channel has the highest average revenue?" — avoids overwhelming the LLM with raw row data.
- **`compute_and_query`:** Adds a derived column using `df.eval()` before filtering or sorting. Used for calculated metrics like ROI (`Revenue Generated / Budget Allocated`) that don't exist as columns.
- **`get_row_index`:** Returns the exact DataFrame index of matching rows before any delete or update, preventing index guessing errors.
- **`find_missing_rows` / `delete_missing_rows`:** Separated into preview and execute tools since `query()` has no `isnull()` support.

## 4. User Experience: Confirmation Preview System
All write operations (add, update, delete) go through a confirmation flow before executing:

- **Why:** Destructive operations are irreversible. Showing a before/after preview lets the user catch model errors before they affect the data.
- **Implementation:** `_execute_tool` intercepts write operations, builds a markdown preview (before/after table, row counts), and returns a `__CONFIRM__:` signal instead of executing. `app.py` catches this signal, displays Chainlit action buttons (✅ Yes / ❌ Cancel), and calls `confirm_pending()` or `cancel_pending()` based on the response.
- **Resuming After Confirmation:** After a confirmed write, `app.py` calls `continue_after_confirm()` on the agent, which re-enters the ReAct loop using the existing conversation history — allowing the agent to continue multi-step tasks (e.g. deleting then adding dummy rows) without re-prompting the user. Nested confirmations within this continuation are also handled.
- **Note on `delete_records`:** The bulk-delete tool (`delete_records`) executes without a confirmation preview in the current implementation, as it falls outside the write-ops guard in `_execute_tool`. This is a known gap — it should be added to the guard in a future revision.
- **`add_records`:** Bulk insert tool accepting a list of dictionaries, mirroring `delete_records`. Avoids the agent needing one ReAct turn per row when inserting multiple records — critical when using free-tier models with rate limits and a 5-turn loop cap.

## 5. Multi-Model Support & Routing
- **Provider Choice:** Three free-tier models are supported — Groq (Llama 3.3 70B), NVIDIA (Llama 3.3 70B Instruct), and Gemini (2.5 Flash Lite) — selectable at session start via Chainlit action buttons.
- **Observed Performance:** Groq significantly outperforms the others for this task due to Llama 3.3's instruction-following strength and Groq's LPU hardware reducing per-turn latency. Since the ReAct loop makes multiple LLM calls per request, low latency per call matters significantly.
- **Abstraction:** `_call_llm` is a provider-agnostic router. The core agent logic is identical regardless of model, with `temperature=0.2` set across all providers for more deterministic tool call formatting.
- **Default Fallback:** If model selection fails, the system defaults to Groq rather than Gemini, since Groq demonstrated the most reliable ReAct formatting during testing.

## 6. Configuration: Environment-Based Security
- **`os.getenv` + `python-dotenv`:** API keys are separated from source code, essential for a public GitHub submission. The app runs locally via `.env` or in any cloud environment where keys are injected as system variables.

## 7. Trade-offs & What I'd Do Differently
- **String Parsing vs JSON Schema:** Tool calls are parsed from LLM text using string splitting and `eval()`. This is fragile — in production I would define strict JSON schemas for each tool and use structured output APIs (where available) to guarantee argument formatting.
- **Positional Arguments Required:** Because tool arguments are parsed via `eval()` on a raw string, the LLM must use positional arguments only — keyword argument syntax (e.g. `file_key='properties'`) causes a syntax error at parse time. This is enforced via a rule in the system prompt with a correct/incorrect example. In production, a proper argument parser per tool would eliminate this constraint.
- **Bulk Insert Added (`add_records`):** Without a bulk insert tool, adding N rows requires N separate ReAct turns, quickly exhausting the 5-turn loop cap and hammering free-tier API rate limits. `add_records` accepts a list of dictionaries and inserts all rows in a single tool call — consistent with how `delete_records` handles bulk deletes.
- **`eval()` Risk:** Using `eval()` to parse tool arguments is convenient but carries security risk if the LLM produces unexpected code. In production this would be replaced with explicit argument parsers per tool.
- **Context Growth:** The full conversation history is injected into every prompt. For long sessions this grows the context window significantly, increasing latency and cost. I would implement a sliding window or summarization step for production use.
- **No Vector Search:** For massive Excel files, loading the full schema into context is inefficient. I would implement a vector database (RAG) to retrieve only relevant rows rather than returning entire filtered tables to the LLM.
- **Single-file Scope:** The two files have no relational link, so cross-file questions (e.g., "which channel works best for high-value properties?") require the LLM to reason across two independent datasets. A proper relational database with JOIN support would handle this more reliably.
- **`delete_records` Confirmation Gap:** The bulk-delete operation currently bypasses the confirmation preview system due to a missing entry in the write-ops guard. Until fixed, bulk deletions are irreversible without user review.