# AI Evaluation Harness - Portfolio Project

A working example of an automated evaluation pipeline for AI-generated text,
built with [DeepEval](https://deepeval.com), evaluating how faithfully an AI
assistant (e.g. Copilot or Claude) summarises a technical report - a realistic
enterprise use case rather than a toy example.

## Why this project

Built to develop genuine, hands-on experience with AI evaluation engineering:
defining metrics, writing automated test cases, catching hallucinations, and
running evaluation as a repeatable CI pipeline rather than a one-off manual
check. This is a deliberate practice project, not a claim of production AI
engineering experience - see the covering note in my CV/cover letter for how
this fits alongside my main background in data platforms and BI.

## What's in here

- `tests/test_report_summary_eval.py` - core evaluation using DeepEval's
  built-in metrics: **Answer Relevancy**, **Faithfulness**, and
  **Hallucination**. Includes one example of a good summary and one with a
  deliberately invented fact, to show the metrics actually catch it.
- `tests/test_custom_geval_metric.py` - a **custom metric** built with G-Eval
  ("Numeric Accuracy"), showing how to translate a specific business quality
  bar (numbers in a summary must be correct) into a measurable evaluation
  criterion - directly relevant to "translate business risk and policy
  requirements into measurable technical evaluation frameworks."
- `.github/workflows/eval.yml` - CI pipeline that runs the evaluation suite
  automatically on every push, so a change to a prompt or model would be
  caught automatically rather than relying on manual review.

## Setup

1. Clone/copy this project, then:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and add an OpenAI API key (DeepEval uses an
   LLM as the "judge" that scores each metric - this costs a small amount of
   API credit per run, typically pennies for this suite).
3. Run the evaluation suite:
   ```bash
   deepeval test run tests/
   ```
   You'll get a pass/fail per metric per test case, with an explanation of
   *why* each metric scored the way it did - this explanation is the useful
   part for understanding failure modes.

## Next steps (Week 2+ of the learning plan)

- [ ] Add a **Promptfoo** config to do prompt regression testing and basic
      red-teaming (jailbreak/prompt injection resistance)
- [ ] Build a tiny **RAG pipeline** (a handful of documents + a vector store
      like Chroma) and evaluate it with **Ragas** metrics (faithfulness,
      context precision/recall)
- [ ] Try swapping the judge model to see how scores change between models
- [ ] Extend the custom metric set to cover other business-specific quality
      bars (e.g. tone, completeness against a checklist, PII leakage)

## Real-world extension idea

Adapt this same pattern to genuinely evaluate a live use case from your own
work - e.g. how well Copilot/Claude summarises a real (anonymised) report you
work with day to day. That turns this from a demo into a genuine, ongoing
evaluation practice you can speak to concretely in interviews.
