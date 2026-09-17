# NOVA
This is very much changed from the original nova which only used gemini-SDK. While we ARE using open-AI sdk instead of https requests like rushil said, it is because we dont need to design the dict parsing and json converting to dict part ourselves, since openAI sdk already does that, and it has the same freedom we were trying to achieve as plain https requests. basically it has the same functionality just a little easier to build/teach

The main idea is simple: the assistant should not be locked to one AI company. NOVA uses one client shape and one tool-calling flow, so you can switch between OpenAI-compatible providers by changing the API key, base URL, and model in `.env`.

NOVA can currently:

- Hold a conversation in the terminal.
- Answer normally through a chat model.
- Search the web and open Google results in the browser.
- Search YouTube and open the results in the browser.
- Ask Tavily for a short search summary when a Tavily key is configured.
- Use the same application code with OpenAI, Groq, Mistral, DeepSeek, Together AI, Fireworks, Cerebras, xAI (Grok), OpenRouter, and other providers that expose an OpenAI-compatible API.

File handling, weather, news, and currency tools are included in the agent tool registry. File operations are restricted to the NOVA workspace.

## The Important Idea: One Compatible Shape

The project does not use separate Google, Mistral, Groq, or provider-specific SDKs in the assistant code. It uses the OpenAI Python client as a common interface and points that client at the provider selected in `.env`.

The provider configuration is deliberately generic:

```env
OPENAI_API_KEY=your_provider_key
OPENAI_BASE_URL=https://provider.example/v1
NOVA_MODEL=the-model-name-you-want
TAVILY_API_KEY=tavilykey (this is completely optional, i thought it would make our model a bit better since itll summarize websearches for us)
```

The variable is called `OPENAI_API_KEY` because that is the name expected by the OpenAI-compatible Python client. It can contain a key from the provider you are using; it does not mean the project is locked to OpenAI.

### Supported provider configuration

| Provider | `OPENAI_BASE_URL` example | Example model names |
| --- | --- | --- |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini`, `gpt-5` |
| Groq | `https://api.groq.com/openai/v1` | Check Groq's current model list |
| Mistral | `https://api.mistral.ai/v1` | `mistral-small-latest`, `mistral-large-latest` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat`, `deepseek-reasoner` |


Provider model names and availability change. `openaimodelcheck.py` can be used to list the models visible to the configured key. this is not as helpful, since it lists ALL the models available, not the ones available to _just_ you with your free tier

## Project Layout

```text
.
├── app.py                         Streamlit entry point
├── main.py                        Terminal entry point
├── agent/
│   ├── nova.py                    Client setup, conversation loop, and tool calling
│   ├── pipeline.py                Request-preparation hooks for intent/RAG work
│   ├── systemprompt.py            NOVA's personality and behavior instructions
│   └── __init__.py                Agent package marker
├── tools/
│   ├── webSearch.py                Web, YouTube, and Wikipedia search tools
│   ├── files.py                    File creation, folder creation, and reading tools
│   ├── weather.py                  Weather API tool
│   ├── news.py                     News headlines API tool
│   ├── currency.py                 Currency conversion API tool
│   ├── client.py                   Shared HTTP helper for API tools
│   ├── toolSchema.py               Converts Python functions into tool schemas
│   ├── __init__.py                 API-tool exports
│   └── ...                          Generated __pycache__ files are omitted
├── dev utils/
│   ├── env.example                 Safe environment-variable template
│   ├── openaimodelcheck.py         Lists models from the configured provider
│   └── test_tools.py                Development tool checks
├── websearchOLDWORKING.py          Legacy web-search implementation
├── NOVA_Work_Division.md           Team responsibilities and work status
├── requirements.txt                Python dependencies
├── .gitignore                      Keeps local secrets and generated files out of Git
└── ...                              Local .env/key files and generated files are omitted
```

## How the Request Works

The runtime flow is intentionally manual and easy to follow:

1. `main.py` loads for running the agent in terminal
2. `createNova()` adds the system prompt as the first message.
3. The user enters a message in the terminal.
4. `askNova()` sends the conversation, model name, and generated tool schemas to the provider.
5. If the model answers normally, NOVA prints the response.
6. If the model requests a tool, NOVA finds the matching Python function in `toolMap` and runs it.
7. The tool result is added to the conversation.
8. NOVA makes one intentional follow-up request so the model can explain what the tool did.

The conversation is stored in the `chat` list while the program is running. It is not saved to a database or file, so closing the program clears the conversation.

## Tool Schemas

The model cannot automatically understand an arbitrary Python function. `tools/toolSchema.py` inspects each function's type hints and docstring and converts it into the JSON schema expected by OpenAI-compatible APIs. (this part was done by AI since i couldnt understand --shit--)

That lets tools stay as ordinary Python functions:

```python
def searchWeb(query: str) -> str:
    ...
```

NOVA turns that into a function tool with a required string argument named `query`. The tool's first docstring line becomes its description, and its `Args:` section supplies the argument description.

To enable a new tool:
### JO BHI LOG TOOL BNARE HO PLS YE PDHLO
1. Write the Python function with type hints and a useful docstring.
2. Import it in `agent/nova.py`.
3. Add it to `toolBox`.
4. Start NOVA again.

The existing file and weather modules are not enabled yet because they are still placeholders.

## Installation

### Requirements

- I BUILD IT ON PYTHON 3.12, PLS EVERYONE FOLLOW THAT AS I FOUND IT MOST STABLE IF WE HAVE TO INCLUDE CNN IN NEAR FUTURE
- A provider API key with access to a chat model.
- Internet access for the model request and web tools.

### 1. Clone the repository

i assume itna toh aata hoga

### 2. Create a virtual environment
vs code me bottom right me it tells u ur interpreter, from there u can decide to make a venv. 
itll ask u to install dependancies, just install requirements.txt from there
rushil, it should work with `uv` now as i tested it, and afaik no version conflict

### 3. Install dependencies
alr done, if not just run `pip install -r requirements.txt`
### 4. Create `.env`

Copy `env.example` to `.env`:
`copy env.example .env`

macOS/Linux:

```bash
cp env.example .env
```

Then edit `.env` with a real key and provider configuration. For example, with Mistral:

```env
OPENAI_API_KEY=your_mistral_key
OPENAI_BASE_URL=https://api.mistral.ai/v1
NOVA_MODEL=mistral-small-latest (use this model only)
TAVILY_API_KEY=
```

For OpenAI, use:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
NOVA_MODEL=gpt-4o-mini (maybe this model is not available for free api tier, i couldnt get it to work)
TAVILY_API_KEY=
```

Do not commit `.env`, paste keys into Python files, or share keys in screenshots or chat. `.gitignore` is configured to ignore local `.env` files.

### 5. Run NOVA

```powershell
python main.py
```

To use the Streamlit chat interface instead:

```powershell
streamlit run app.py
```

The web interface keeps the conversation in Streamlit session state and
reuses the same agent and tool-calling flow as terminal mode. Request
preparation is isolated in `agent/pipeline.py`, which currently preserves the
existing behavior and provides extension points for the planned intent
classifier and retrieval-augmented generation (RAG) layer.

You should see:

```text
NOVA (terminal mode). Type 'quit' to exit.

You:
```

Type `quit` to leave the program.

## Optional: Web Search Summaries

The web tools always open the browser. If `TAVILY_API_KEY` is empty, NOVA still opens the search page but returns a message explaining that no spoken summary was generated.

To enable summaries, add a Tavily key:

```env
TAVILY_API_KEY=your_tavily_key
```

Tavily is separate from the chat provider. This was a deliberate choice: provider-specific web-search features would make switching between model providers less portable. Tavily gives the project one ordinary REST API for search summaries regardless of which model answers the conversation.

## Check Available Models

With `.env` configured, run:

```powershell
python openaimodelcheck.py
```

This calls the configured provider's model-list endpoint and prints the model IDs visible to that key. Choose one of those IDs for `NOVA_MODEL`.

## Problems We Ran Into

### Moving away from the Google SDK

The earlier approach used a Google-specific SDK. That made the project harder to move between providers and tied the tool behavior to one vendor's conventions. NOVA was moved to the OpenAI-compatible Chat Completions shape instead.

meri halat tight hogyi switching me, i should not have taken it as a one day endeavor when idk shit abt openAI sdk

The tradeoff is that tool schemas now have to be generated manually. That is what `functionToToolSchema()` handles.

### An empty base URL caused connection errors

An `.env` line like this looks harmless:

```env
OPENAI_BASE_URL=
```

With the installed SDK, an empty value can override the SDK's default URL and produce a connection error about a missing `http://` or `https://` protocol. NOVA now removes an empty base URL and lets the client use its default endpoint. For a custom provider, the URL must be complete and include `https://`.

### Provider rate limits looked like a code failure

The OpenAI-compatible client maps a provider's HTTP 429 response to `RateLimitError`, even when the provider is Mistral, Groq, or another service. NOVA originally displayed that as an OpenAI-style usage-limit message, which made the diagnosis confusing.

The message now says which provider rate-limited the request. A newly created key can still have a zero request limit if its workspace, billing, verification, or provider account is restricted. Listing models can work while chat inference is rate-limited.


### Hidden retries could repeat requests

The OpenAI Python client has its own automatic retry behavior. NOVA also had an explicit retry loop. That made it difficult to tell how many requests one input could create. SDK retries are now disabled with `max_retries=0`, and NOVA defaults to one attempt per user message.

The only normal two-request flow is intentional tool use: one request to choose a tool and one request to produce the final answer after the tool runs.

## Editing NOVA's Personality

The assistant's personality is in `agent/systemprompt.py`. You can make it more direct, more chatty, or more formal without changing the core request and tool-calling code.

The important rule is to keep the tool instructions intact. If the prompt says the assistant should use a tool when the user asks it to perform an action, the model is more likely to call the correct function instead of merely describing what it could do.

## Current Limitations

- The interface is available in terminal mode and Streamlit.
- Conversation history disappears when the process exits.
- Tools include web, YouTube, Wikipedia, file, weather, news, and currency operations.
- Browser searches depend on the machine's default browser.
- Tavily summaries require a separate key.
- Provider model names, quotas, and rate limits are controlled by each provider.
- The project assumes the selected provider supports the OpenAI-compatible Chat Completions and function-tool format.

## A Note for Contributors

Keep provider-specific setup in environment variables and keep the Python request path provider-neutral. When adding a tool, use a typed function and a clear docstring so the schema generator can describe it to the model.

The project is intentionally readable rather than over-engineered. Some comments are informal because this was built while learning and debugging the system. They document real decisions: why the provider interface was changed, why Tavily is separate, why tool arguments are decoded with JSON, and why the client retry behavior is controlled explicitly.

## License
MIT license

## NOVA API Tools (P4)

### Import

```python
from tools import get_weather, get_news, convert_currency
```

### Contract

All functions take simple arguments, return a plain string, and never raise.
Failures return a readable sentence, so the agent can speak them directly.

### Functions

#### `get_weather(city: str) -> str`

Current weather for a city.

- `city`: city name, for example `Delhi`

Example: `Delhi: 30 degrees, broken clouds. Feels like 37, humidity 84 percent.`

#### `get_news(topic: str = "", count: int = 5) -> str`

Current headlines. Leave `topic` empty for general news.

- `topic`: optional. Recognised categories are `general`, `world`, `nation`,
  `business`, `technology`, `entertainment`, `sports`, `science`, and `health`.
  Anything else is treated as a keyword search.
- `count`: number of headlines from 1 to 10. Values outside that range are clamped.

Example: `Here are the top headlines:\n1. ...\n2. ...`

#### `convert_currency(amount: float, from_currency: str, to_currency: str) -> str`

Convert between currencies using live rates.

- `amount`: number greater than zero
- `from_currency` and `to_currency`: 3-letter codes, for example `USD` and `INR`

Example: `500 USD is about 47,837.27 INR.`

The agent must map spoken words to codes, such as `rupees` to `INR`.

### API Tool Setup

Install the direct dependencies with:

```powershell
pip install requests python-dotenv
```

Copy `.env.example` to `.env` and fill in:

```env
OPENWEATHER_API_KEY=
GNEWS_API_KEY=
```

Currency conversion uses a public exchange-rate endpoint and does not need an API key.

### API Tool Testing

Run the standalone API-tool checks with:

```powershell
python -m tools.test_tools
```
