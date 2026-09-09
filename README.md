# claude-tools

A small multi-agent research coordinator built on the Claude API. A `Coordinator`
decomposes a topic into subtopics, delegates each one to specialist subagents
running concurrently, and iteratively re-researches any subtopics with
insufficient coverage.

## How it works

1. `Coordinator.decompose()` asks Claude to break a research topic into
   subtopics, covering both mainstream and emerging/experimental approaches.
2. For each subtopic, `Coordinator.delegate_to_subagents()` runs both
   subagents concurrently:
   - **`web_search_agent`** — uses a mock `web_search` tool to gather findings.
   - **`doc_analysis_agent`** — uses a mock `search_documents` tool to gather
     findings from internal docs.
3. `Coordinator.evaluate_coverage()` checks which subtopics have findings and
   which don't. Any gaps are re-researched, up to 3 refinement iterations.

Both tools return mocked data — no real network search or document store is
wired up, so results are useful for exercising the coordination logic, not for
real research.

## Project structure

```
src/
├── coordinator.py           # Coordinator: decompose, delegate, evaluate coverage
├── claude.py                 # Shared Anthropic client (loads ANTHROPIC_API_KEY)
├── main.py                    # CLI entry point
├── agents/
│   ├── web_search_agent.py   # Agent backed by the web_search tool
│   └── doc_analysis_agent.py # Agent backed by the search_documents tool
└── tools/
    ├── web_search.py          # Mock web search tool
    └── calculator.py          # Calculator tool (unused, but safe to wire up)
tests/
└── test_coordinator.py       # End-to-end coverage test (hits the real API)
```

## Setup

Requires Python >= 3.11 and [Poetry](https://python-poetry.org/).

```bash
poetry install
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY
```

## Running

```bash
poetry run python src/main.py "renewable energy technologies"
```

## Testing

```bash
poetry run pytest -v
```

The test makes real calls to the Anthropic API and will incur usage costs.
The model used is controlled by the `MODEL` constant at the top of
`coordinator.py`, `agents/web_search_agent.py`, and `agents/doc_analysis_agent.py`:

- `claude-haiku-4-5` — cheap and fast, good for iterating on prompt/logic changes.
- `claude-sonnet-5` — higher quality decomposition and findings; switch to this
  before a final/graded run.

All three files must be set to the same tier for `output_config.effort` to
apply consistently (it's a no-op on Haiku, since Haiku doesn't run adaptive
thinking by default).

