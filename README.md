# NOVA

NOVA is a provider-independent desktop assistant. It combines an OpenAI-compatible chat model with ordinary Python tools. The model interprets natural-language requests and chooses tools; the tools perform the actual work.

NOVA has two interfaces:

- `main.py`: terminal mode with TF-IDF routing for simple tool requests.
- `app.py`: Streamlit chat interface with document upload and RAG support.

## Features

- OpenAI-compatible providers through one client interface.
- Web, YouTube, and Wikipedia search.
- File and folder operations.
- Weather, news, and currency tools.
- Persistent key-value memory.
- PDF, PPTX, TXT, and Markdown document ingestion.
- ChromaDB retrieval for questions about uploaded documents.
- Optional classifier routing that avoids the model for predictable requests.
- Optional provider/model fallback.

## Project Layout

```text
.
|-- main.py                  Terminal entry point and direct classifier routing
|-- app.py                   Streamlit entry point
|-- requirements.txt         Python dependencies
|-- .env.example             Environment-variable template
|-- docs/
|   `-- WORK_DIVISION.md     Historical team responsibilities and notes
|-- agent/
|   |-- nova.py              Client, conversation loop, tool calling, fallback
|   |-- fallback.py          Safe tool calls and provider error helpers
|   |-- pipeline.py          RAG request preparation for Streamlit
|   |-- systemprompt.py      NOVA behavior and personality prompt
|   `-- __init__.py
|-- tools/
|   |-- toolSchema.py        Converts Python functions to model tool schemas
|   |-- webSearch.py         Web, YouTube, and Wikipedia tools
|   |-- files.py             File and folder tools
|   |-- weather.py           Weather API tool
|   |-- news.py              News API tool
|   |-- currency.py          Currency conversion tool
|   |-- client.py            Shared HTTP helper
|   |-- classifier.py        TF-IDF classifier loader and predictor
|   |-- memory.py            Persistent user memory
|   |-- rag.py               Document extraction, chunking, and retrieval
|   `-- model/               Trained classifier and vectorizer artifacts
|-- dev_utils/
|   |-- openaimodelcheck.py  Lists models exposed by the configured provider
|   `-- test_tools.py        Development checks for tools
|-- chroma_db/               Local ChromaDB data, generated at runtime
|-- temp_uploads/            Uploaded documents, generated at runtime
|-- nova_memory.json         Local memory file, generated at runtime
```

`chroma_db/`, `temp_uploads/`, `nova_memory.json`, `.env`, and Python cache files are local state. They should not be committed. Existing local files are left in place so uploaded study material is not accidentally deleted.

There is one environment template at the project root: `.env.example`. Copy it to `.env` for local use. The `dev_utils/` directory contains scripts only; it does not contain a second configuration template.

## Setup

Use Python 3.12, which is the version used to develop and test this project.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, run this once in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### macOS or Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with a provider key and model. The key variable is named `OPENAI_API_KEY` because that is what the OpenAI-compatible Python client expects; it can contain a key from another compatible provider.

```env
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
NOVA_MODEL=your_model_name
NOVA_FALLBACK_MODEL=
TAVILY_API_KEY=
OPENWEATHER_API_KEY=
GNEWS_API_KEY=
NOVA_CHROMA_PATH=./chroma_db
```

For real OpenAI, use `https://api.openai.com/v1`. For another provider, use that provider's documented OpenAI-compatible base URL and model name. Provider model names and availability change, so check the provider's current documentation.

## Running NOVA

Terminal mode:

```powershell
.\.venv\Scripts\python.exe main.py
```

Streamlit mode:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The terminal classifier can directly route high-confidence requests such as weather, news, currency, file, and search requests. Ambiguous requests are sent to the AI agent. Streamlit uses the agent for conversation and prepares document questions through `agent/pipeline.py`.

## Request Flow

### Terminal mode

1. `main.py` loads the trained TF-IDF vectorizer and classifier.
2. The classifier returns a tool label or `LLM`/unknown intent.
3. Simple requests are parsed by `directArguments()` and call a tool directly.
4. Ambiguous requests call `askNova()`.

### Agent mode

1. `createNova()` creates a message list containing the system prompt and saved memory.
2. `askNova()` sends the conversation and `toolSchemas` to the configured model.
3. The model may return one or more tool calls.
4. `toolMap` resolves each function name to a Python function.
5. The function result is added to the conversation.
6. A follow-up model request turns the result into a user-facing answer.

## How To Add A Tool

1. Add a normal Python function under `tools/`.
2. Give it type hints and a useful docstring.
3. Put the description on the first docstring line.
4. Describe parameters in an `Args:` section.
5. Make the function return a readable string and handle expected errors itself.
6. Import it in `agent/nova.py`.
7. Add it to `toolBox`.
8. If the tool should be callable without the AI, add its classifier label and argument parsing to `main.py`.
9. Run the checks below.

Example:

```python
def greet(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}."
```

`tools/toolSchema.py` converts the function signature and docstring into the schema sent to the model. Do not manually duplicate the schema in `nova.py`.

## How To Change Existing Behavior

- Personality and response style: edit `agent/systemprompt.py`.
- Model/provider behavior: edit environment variables first; edit `agent/nova.py` only for shared request behavior.
- Tool registration: edit `toolBox` in `agent/nova.py`.
- Direct terminal routing: edit the classifier artifacts or `main.py`.
- RAG intent detection and context preparation: edit `agent/pipeline.py`.
- Document extraction, chunking, or retrieval: edit `tools/rag.py`.
- Memory storage format: edit `tools/memory.py`. Existing `nova_memory.json` may need migration if its format changes.
- Streamlit layout and upload workflow: edit `app.py`.
- Dependencies: update `requirements.txt`, then reinstall them in the active virtual environment.

Keep provider calls, tool registration, and UI code separate. A tool should remain usable directly from Python even when no AI model is configured.

## Validation

Run these commands from the project root:

```powershell
.\.venv\Scripts\python.exe -m compileall -q agent tools app.py main.py
.\.venv\Scripts\python.exe dev_utils\test_tools.py
.\.venv\Scripts\python.exe -m pip check
```

Before committing, also check:

```powershell
git status
git diff --check
```

Do not commit API keys, `.env`, uploaded documents, ChromaDB files, memory files, or generated caches. Do not commit unresolved conflict markers.

## Model List Helper

With `.env` configured, run:

```powershell
.\.venv\Scripts\python.exe dev_utils\openaimodelcheck.py
```

This lists models visible to the configured provider. It does not guarantee that every listed model is enabled for inference or available under a free tier.

## Troubleshooting

- Missing `OPENAI_API_KEY`: copy `.env.example` to `.env` and add a provider key.
- Model not found: set `NOVA_MODEL` to a model available from the configured provider.
- Provider connection error: check that `OPENAI_BASE_URL` is either blank or a complete URL beginning with `https://`.
- Missing weather/news output: configure `OPENWEATHER_API_KEY` or `GNEWS_API_KEY`. Weather falls back to Google/Tavily search when the OpenWeather key is blank.
- RAG import or embedding errors: reinstall `requirements.txt`; the first embedding use may download a sentence-transformers model.
- Classifier loading errors: use the same Python environment that installed `joblib` and `scikit-learn`.
- Stale document results: remove the local `chroma_db/` directory and re-upload the documents. This clears only the local vector index.
