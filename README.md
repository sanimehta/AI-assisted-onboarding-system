# AI-Assisted Onboarding System (fictional platform)

Onboarding a new customer to an integration platform means reading a request email, working out what the customer needs, and then setting up the same project structure with a few values changed. This project automates the repeatable parts on a **fictional platform with invented customers**.

An LLM reads the customer's email and extracts a structured request. A person reviews it. Plain code then builds the project from a template and validates the output. The AI handles the one step where the input is messy, and ordinary code handles everything that has to be exact.

> This is a personal learning project. The platform, file formats, customers, and emails are all invented. It does not use any real company's systems, data, or conventions, and it is a local prototype, not a production system.

## How it works

```
customer email
   |
   v
[LLM] extract a structured request  -->  human reviews and approves
   |
   v
propose a chain code  -->  generate project from template  -->  validators
   |
   v
new project folder (or a clear list of errors)
```

## Where AI is used, and where it is not

| Step | Done by | Why |
|---|---|---|
| Read the email and extract the request | LLM | Customers phrase the same thing many different ways |
| Say "unknown" instead of guessing | LLM, prompted to return null and ask a question | Missing details should go back to a human |
| Look up document-code jargon and similar past requests | Retrieval (Chroma) | Gives the model reference material at question time |
| Check the model's answer and retry once on errors | Plain code | The model's output is validated, never trusted |
| Propose a chain code | Plain code | Deterministic and checkable |
| Build the project from a template | Plain code | Must be exact |
| Validate the generated project | Plain code | A checker should not be the same kind of thing that made the mistake |
| Approve the request | Human | Nothing is built until a person confirms |

## Agent version (ADK)

The same extraction task, rebuilt as an ADK agent that calls the MCP server's tools instead of running a fixed pipeline:

```
customer email
   |
   v
[ADK agent, Gemini] extract the request
   |  (only if customer_name, docs, format and ftp_owner are all known)
   v
suggest_chain --> check_spec --> preview_project  --> JSON for human review
```

The agent's instruction contains the same document codes and field rules as the pipeline's prompt. It has no retrieval step. It only has the three read-only tools, so it cannot save a project or reserve a chain. That still happens only in the command-line flow, after a person approves.

## Stack

Python, [Ollama](https://ollama.com) (`qwen2.5:7b` for extraction, `nomic-embed-text` for embeddings), Pydantic, Chroma (vector database), the MCP Python SDK, and Google's Agent Development Kit (ADK). The pipeline is open source and runs locally. The agent version calls a hosted Gemini model through a free-tier Google AI Studio key, so it is the only part that sends data off the machine (all of it fictional).

## Run it

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

python -m venv .venv
.venv/Scripts/Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install ollama chromadb pydantic 'mcp[cli]'

python -m scripts.make_templates    # creates the template project and chain registry
python -m scripts.eval_generator    # tests the generator and validators
python -m scripts.build_library     # indexes the glossary and past requests in Chroma
python -m scripts.eval_extraction rag        # scores extraction on all 18 emails
python -m scripts.eval_extraction rag new    # scores only the 6 held-out emails
python -m scripts.onboard_cli data/sample_email.txt   # full flow with a human approval step
python -m tests.test_mcp_tools      # checks the MCP tools, including that preview saves nothing
```

Agent version (needs a free key from [Google AI Studio](https://aistudio.google.com)):

```bash
pip install google-adk python-dotenv 'mcp<2'
# put GOOGLE_API_KEY=... and GOOGLE_GENAI_USE_VERTEXAI=FALSE in onboarding_agent/.env (not committed)
adk run onboarding_agent                 # chat with the agent
python -m scripts.eval_agent new         # score it on the 6 held-out emails
python -m scripts.eval_agent             # score it on all 18
```

Run all commands from the project root. To use the MCP server, run `npx @modelcontextprotocol/inspector python mcp_server.py` (requires Node.js).

### MCP server

`mcp_server.py` exposes three tools: `check_spec` (validate a request), `suggest_chain` (propose an unused chain code), and `preview_project` (build in a temporary folder and report errors). All three are read-only on purpose. Saving a project and reserving a chain only happen in the command-line flow, after a person approves.

## Results

### Generator and validators

10 of 10 test specs behaved as expected: 4 valid specs built correctly and 6 invalid specs (chain too long, lowercase chain, chain already in use, unsupported document, no documents, unknown format) were rejected with clear errors. Editing a template so the chain no longer matched made the tests fail, which confirms the output check catches real errors.

### Email extraction

**Development set (12 emails, glossary written after seeing them)**

| System | Exact match | customer_name | docs | format | ftp_owner |
|---|---|---|---|---|---|
| Keyword rules (baseline) | 2/12 | not scored | 2/12 | 10/12 | 6/12 |
| LLM | 10/12 | 12/12 | 10/12 | 12/12 | 12/12 |
| LLM + glossary only | 9/12 | 12/12 | 10/12 | 12/12 | 11/12 |
| LLM + glossary + similar past requests | 11/12 | 12/12 | 12/12 | 12/12 | 11/12 |
| ADK agent (Gemini, MCP tools, no retrieval) | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 |

**Held-out set (6 emails written after the library was built)**

| System | Exact match | customer_name | docs | format | ftp_owner |
|---|---|---|---|---|---|
| Keyword rules (baseline) | 1/6 | not scored | 2/6 | 6/6 | 1/6 |
| LLM | 4/6 | 6/6 | 5/6 | 6/6 | 4/6 |
| LLM + retrieval | 5/6 | 6/6 | 6/6 | 6/6 | 5/6 |
| ADK agent (Gemini, MCP tools, no retrieval) | 5/6 | 6/6 | 6/6 | 5/6 | 6/6 |

The ADK agent matched the best pipeline on this data: 17/18 exact overall, against 16/18 for LLM + retrieval. That is a one-email difference on tests I wrote myself, so I do not read it as the agent being better. It made about 3.7 model calls and 2.7 tool calls per email (the pipeline makes one call, plus one retry on invalid output) and took about 32 seconds per email on a free-tier key. That figure varies with load and is not comparable to the local timings. Its only miss was the format field on one held-out email. A first held-out run used an instruction with two extra rules (ignore cancelled documents, ignore phone numbers and addresses); it scored the same 5/6, and I removed the rules so the agent gets no information the pipeline lacks.

The model alone took roughly 11 to 17 seconds per email on my laptop, and retrieval added about 40% to 75% on top of that across runs. The test sets are small and written by me, so these results show direction, not statistical significance.

The emails include deliberate traps: a document that was requested and then cancelled, a phone number and a street address that contain document codes, a customer who has not decided who hosts the server, descriptions of documents without their numbers, and an email with almost no information.

## What went wrong, and what I changed

- **First run: 7/12 exact match.** Several answers were discarded even though the model had read the email correctly. The model returned `"questions": null`, and my code only accepted a list. Fixing the parsing so empty values are normalized brought the score to 10/12.
- **A mistake in my first parsing fix scored 0/12.** Every answer failed to parse and was retried (12 retries), but the retry loop's error handling hid the real error message. I called the parser directly, without the error handling, to see the actual exception, then corrected the code. The lesson: broad try/except blocks can hide the cause of a failure.
- **The model returned the text "null" instead of an empty value** for fields it did not know, which let an unanswered question slip past the human prompt. I now convert "null", "none", and "unknown" to a real empty value in code.
- **First retrieval attempt returned only past emails, never the glossary.** Long email-style queries ranked other emails above the short glossary notes. Retrieving the two kinds separately fixed that.
- **The glossary alone did not help a 7B model; similar solved examples did.** Document-name cases that were missed with the right glossary note in the prompt were fixed once similar past requests were included. Because some of those examples were written with related wording, the held-out set is the fairer evidence.
- **Retrieval made one email more cautious.** On one email, the model returned no hosting answer and asked a question instead of reading "our server team will email the details." The human review step catches this, but it shows added context can push a small model toward abstaining.
- **One held-out email is ambiguous.** Both LLM versions disagreed with my expected hosting answer on an email saying "we will set up the server on our side once we know your IP." I did not change my expected answer after seeing the result.
- **The agent invented a format.** On one held-out email that never states a format (expected answer: null), the agent answered `xml`. `check_spec` accepted it because `xml` is an allowed value, so the agent built a preview with a value that did not come from the email. The validators check that a value is allowed, not that it was stated, so only the human review step would catch this. I did not change the prompt and rerun.
- **My first agent evaluation scored 0/6 because nothing ran.** The script did not load the API key, so every call failed in a fraction of a second. The model-call count of 0 per email gave it away. `adk run` loads the `.env` file automatically and a plain Python script does not.
- **Free-tier latency made the agent look frozen.** At one point a one-word request took about 42 seconds, and the 4-call agent loop took minutes. Adding a per-email timeout and a delay between emails fixed the evaluation script.

## Limitations

- The platform, emails, and expected answers are all written by me, so the results are optimistic. The test sets are small (12 and 6 emails).
- The keyword baseline is deliberately simple. A version with synonym lists would score higher.
- A local 7B model is slower and less accurate than larger hosted models, and run-to-run timing varies.
- This is a prototype. It has not been deployed, load tested, or used with real customer data.
- The agent and the pipeline differ in two ways at once: the design (tool-calling agent vs. one fixed call) and the model (hosted Gemini vs. a local 7B). This comparison cannot separate them.
- The agent results are from a single run with no fixed temperature, and the agent gets one attempt per email while the pipeline retries once on invalid output.
- The agent derives `project_name` from the customer name in its prompt, and that field is not scored.

## Next steps

- Add a second template pattern and have the system choose between templates
- Run the agent on Google Cloud (Vertex AI) instead of an AI Studio key, and trace tool calls and token usage
- Repeat the agent evaluation with a fixed temperature and several runs per email, since the current numbers come from a single run