# Week 3 - RAG Pipeline + Ragas

A small, real, end-to-end RAG (Retrieval-Augmented Generation) system,
evaluated with [Ragas](https://docs.ragas.io) - the standard framework
for RAG-specific evaluation metrics.

## What's here

- `documents.py` - a small "internal knowledge base" (6 short docs about
  Fabric/Power BI platform issues - Dataflow locks, RLS for guest users,
  capacity throttling, gateway permissions, Direct Lake, staging table
  growth).
- `build_index.py` - embeds the documents (OpenAI embeddings) and stores
  them in a local Chroma vector database.
- `query_and_evaluate.py` - runs three test questions through the full
  RAG pipeline (retrieve -> generate), then evaluates the results with
  four Ragas metrics.
- `patch_ragas_bug.py` - a one-time fix for a real, currently-open bug in
  Ragas (see below) - kept here deliberately as evidence of real
  troubleshooting, not swept under the rug.

## A known bug you'll hit, and why this is actually a good thing to show

As of the `ragas==0.3.9` version pinned in `requirements.txt`, simply
running `import ragas` crashes with:

```
ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'
```

This happens for **every** user, including ones (like this project) that
only use OpenAI and have never touched Google VertexAI. The cause: Ragas
unconditionally imports a VertexAI integration class from a path that
newer versions of `langchain-community` removed
([upstream issue](https://github.com/vibrantlabsai/ragas/issues/2745),
unresolved as of writing).

**Fix**: run this once, after installing requirements:

```bash
python patch_ragas_bug.py
```

This patches the installed Ragas package to make that import optional
instead of a hard crash (verified safe: the removed class was only used
in an `isinstance()` check for VertexAI-specific models, which this
project never uses). It's safe to re-run - it detects if it's already
patched.

This is left in the repo on purpose rather than quietly worked around,
because diagnosing and fixing a real upstream dependency bug - not just
using a library when everything already works - is a genuine, relevant
skill for this kind of role.

## Setup

**Two-step install is required** - ragas is deliberately installed
separately, without its full dependency tree:

```bash
pip install -r ../requirements.txt
pip install ragas==0.3.9 --no-deps
python patch_ragas_bug.py
```

### Why the `--no-deps` step - a second real issue, also worth knowing about

Ragas depends on `scikit-network`, a graph analysis library, for its
synthetic test-set generation feature (which this project doesn't use -
we write test questions by hand). `scikit-network` ships no prebuilt
wheel for very new Python versions on Windows, so a normal install tries
to **compile it from source**, which requires Microsoft's C++ Build Tools
- a multi-GB download most people won't have installed, purely to satisfy
a feature this project never calls.

Installing `ragas==0.3.9 --no-deps`, then letting the base
`requirements.txt` supply ragas's *actual* runtime dependencies (already
listed there), avoids ever needing scikit-network or a C++ compiler at
all. Verified: the four metrics this project uses (`Faithfulness`,
`AnswerRelevancy`, `ContextPrecision`, `ContextRecall`) import and run
fine without it.

Make sure your `.env` (with `OPENAI_API_KEY`) is either in this folder
or one level up - `query_and_evaluate.py` and `build_index.py` both load
it automatically via `python-dotenv`.

## Run it

```bash
python build_index.py
python query_and_evaluate.py
```

## The four metrics, and why both retrieval AND generation matter

| Metric | What it checks | If this is bad... |
|---|---|---|
| **Faithfulness** | Is the generated answer actually supported by the retrieved context? | ...the LLM is hallucinating or embellishing - a **generation** problem |
| **Answer Relevancy** | Does the answer actually address the question asked? | ...the LLM is going off-topic - a **generation** problem |
| **Context Precision** | Are the retrieved chunks actually relevant to the question? | ...embeddings/chunking/retrieval need work - a **retrieval** problem |
| **Context Recall** | Did retrieval find what was needed to answer correctly, judged against a reference answer? | ...retrieval is missing the right chunk entirely - a **retrieval** problem |

Splitting these apart matters in practice: a bad RAG answer could be
fixed by improving the prompt, or it could need better chunking/embeddings
entirely - and those are different fixes made by different people.

## A deliberate test case: the out-of-scope question

One test question ("What's the capital of France?") is **not** covered by
the knowledge base on purpose. A good RAG system should say "I don't have
that information" rather than fall back on the LLM's general knowledge -
watch what `Faithfulness` and `Context Precision` do on that specific
row in `ragas_results.csv` once you've run it; it's a good way to see
whether the "only use the provided context" instruction is actually being
respected.
## A second worked example: Answer Relevancy penalizes correct refusals

On the deliberately out-of-scope question ("What's the capital of
France?"), the assistant correctly refused to answer rather than
hallucinate. Faithfulness/Context Recall reflected this correctly, but
Answer Relevancy scored the refusal 0.0 - because the metric measures
semantic similarity between the answer and the question, and a refusal
genuinely isn't "about" the question topic in that sense.

This is a real limitation worth knowing: Answer Relevancy alone can't
distinguish "wrong/off-topic answer" from "correct refusal" - both score
low. In a production system, you'd want a second, purpose-built check
(e.g. a custom metric or rule) specifically for whether a refusal was
appropriate, rather than relying on Answer Relevancy to catch it.