# Week 4 - Evaluating an AI Agent (Tool Use / Agentic Layer)

Weeks 1-3 evaluated **single LLM calls** - is this one output good? This
week evaluates something structurally different: an **agent** that
decides, step by step, which tools to call, with what arguments, in what
order, to solve a task. A wrong tool choice, wrong arguments, or an
unnecessary tool call can all produce a plausible-sounding final answer
while still being a real failure - which is exactly why "agentic AI
evaluation" is increasingly called out as a distinct skill in job specs,
separate from general LLM evaluation.

## What's here

- `tools.py` - three tools for a small IT support agent: search the
  Week 3 knowledge base, check live system status (mocked), or create a
  support ticket (mocked).
- `agent.py` - a minimal multi-step tool-calling agent loop, built
  directly on OpenAI's native function-calling API (deliberately not
  using a heavy agent framework, so every reasoning/tool-call step stays
  visible and inspectable for evaluation).
- `test_agent_eval.py` - four test cases, each targeting a different
  agent failure mode (see below).

## Setup

```bash
pip install -r ../requirements.txt
```

Requires the Week 3 knowledge base to exist (`../rag/chroma_db`) - run
`python ../rag/build_index.py` first if you haven't already.

## Run it

```bash
deepeval test run test_agent_eval.py
```

## The three metrics, and what each one catches

| Metric | Question it answers | Catches |
|---|---|---|
| **Tool Correctness** | Did the agent call the *right* tools? | Wrong tool chosen, missing tool call, or an unnecessary extra tool call |
| **Argument Correctness** | Were the *arguments* to those tools right? | Right tool, wrong input (e.g. checking status for the wrong system name) |
| **Task Completion** | Did the agent actually *solve* the task end to end? | A technically-correct tool call that still doesn't add up to a useful final answer |

A single "did it work?" check would miss the difference between these -
this is the same "retrieval vs. generation" split from Week 3's RAG
metrics, just one layer up: tool *selection* vs tool *use* vs overall
*outcome*.

## The four test cases

1. **Knowledge question** - "why is X stuck?" should trigger the
   knowledge base search only, not a live status check or a ticket.
2. **Live status question** - "is X down right now?" should trigger a
   status check, not just a documentation search.
3. **Explicit escalation** - a multi-step case where the user has
   already self-served and explicitly asks to log a ticket; the agent
   should go straight to ticket creation rather than redundantly
   re-searching the knowledge base.
4. **The trap case** - a question with no relevant tool at all ("what's
   a good name for a pet goldfish?"). Tests whether the agent correctly
   calls *no* tool, rather than forcing an irrelevant one - over-eager
   tool use is as much a failure mode as under-use.

## A worked example: a gap in the eval setup itself

The first run of this suite passed 4/4 - but the `ToolCorrectnessMetric`
reasoning included a telling line: *"No available tools were provided
to assess tool selection criteria."* Without passing the `available_tools`
parameter, the metric only checks "were the *expected* tools called" -
not "did the agent also call any *other, unnecessary* tools alongside
them." A passing agent could in principle call an irrelevant extra tool
and still score 1.0, as long as it also happened to hit the expected
one.

Fix: pass `available_tools` (all three tools the agent has access to) to
`ToolCorrectnessMetric`, so it can properly evaluate tool *selection* -
whether the agent chose *only* the right tool(s), not just *at least*
the right one(s). This is now reflected in `test_agent_eval.py`.

This is worth keeping in the writeup deliberately: it's a genuine example
of reviewing your own evaluation setup critically rather than treating a
100% pass rate as automatically meaning the harness is complete - the
metric being available doesn't mean it's configured to check everything
it's capable of checking.

## What to look at once you've run it

- Which test case(s) fail, and whether `ArgumentCorrectness` or
  `ToolCorrectness` is the one flagging it - that tells you whether the
  agent chose the wrong action or took the right action with the wrong
  inputs, which point to different fixes (tool descriptions vs. prompt
  clarity).
- Try deliberately weakening a tool's description in `tools.py` (e.g.
  make `check_system_status` and `search_knowledge_base` sound more
  similar) and re-run - watching Tool Correctness degrade is a concrete
  way to see why clear tool descriptions matter as much as the prompt
  itself in agent design.
