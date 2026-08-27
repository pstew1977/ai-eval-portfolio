"""
AI Evaluation Harness - Example: Evaluating an AI assistant's summary of a
data platform incident report against the source document.

This mirrors a real, common enterprise use case: an analyst asks Copilot/Claude
to summarise a technical report (e.g. a data quality investigation, an incident
write-up, a capacity review), and we need to check the summary is accurate,
relevant, and doesn't invent facts that aren't in the source.

Run with:
    deepeval test run tests/test_report_summary_eval.py

Requires an LLM judge. By default DeepEval uses OpenAI, so set:
    export OPENAI_API_KEY=sk-...
(See README.md for using a different provider.)
"""

from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
)
from deepeval.test_case import LLMTestCase

# ---------------------------------------------------------------------------
# Source document (the "ground truth" the AI assistant was asked to summarise)
# ---------------------------------------------------------------------------
SOURCE_REPORT = """
Incident Summary - Data Pipeline Failure, Dataflow Gen2 'df_WAREHOUSE_1'

On the morning of the incident, the scheduled refresh for df_WAREHOUSE_1 failed
to complete. Investigation traced the failure to an orphaned job lock caused by
a separate process inside the same workspace that had not released its lock
after a previous run. The affected dataflow, along with two dependent
dataflows, were stuck in a queued state for approximately six hours.

Resolution involved manually terminating the hung process, which cleared the
lock and allowed the scheduled refreshes to resume. Three dataflows were
confirmed to have recovered successfully following the fix. No data loss
occurred; the only impact was a delay in report freshness for downstream
dashboards during the affected window. A secondary finding was that gateway
permissions were missing for two of the three on-premises data sources used
by this workspace, which should be remediated separately to reduce the risk
of similar failures in future.
"""

# ---------------------------------------------------------------------------
# Example 1: A GOOD summary (faithful, relevant, no invented facts)
# ---------------------------------------------------------------------------
def test_good_summary_passes_evaluation():
    prompt = "Summarise this incident report in 3 sentences for a non-technical stakeholder."

    ai_summary = (
        "A scheduled data refresh failed because a stuck process was holding a lock "
        "in the workspace, blocking three related dataflows for about six hours. "
        "The issue was fixed by manually clearing the stuck process, and all three "
        "dataflows recovered with no data loss, though dashboards were temporarily "
        "out of date. A separate gap in data source permissions was also flagged for "
        "follow-up to reduce the chance of this happening again."
    )

    test_case = LLMTestCase(
        input=prompt,
        actual_output=ai_summary,
        context=[SOURCE_REPORT],
        retrieval_context=[SOURCE_REPORT],
    )

    relevancy = AnswerRelevancyMetric(threshold=0.7)
    faithfulness = FaithfulnessMetric(threshold=0.7)
    hallucination = HallucinationMetric(threshold=0.3)  # lower = stricter

    assert_test(test_case, [relevancy, faithfulness, hallucination])


# ---------------------------------------------------------------------------
# Example 2: A summary with an INVENTED fact (should fail faithfulness/hallucination)
# ---------------------------------------------------------------------------
def test_summary_with_invented_fact_should_fail():
    prompt = "Summarise this incident report in 3 sentences for a non-technical stakeholder."

    # Note: this summary invents a root cause ("a failed Windows update") that is
    # NOT in the source report - a classic hallucination this harness should catch.
    ai_summary_with_hallucination = (
        "A scheduled data refresh failed after a failed Windows update corrupted "
        "the workspace configuration, blocking three related dataflows for about "
        "six hours. The issue was fixed by restarting the server, and all three "
        "dataflows recovered with no data loss."
    )

    test_case = LLMTestCase(
        input=prompt,
        actual_output=ai_summary_with_hallucination,
        context=[SOURCE_REPORT],
        retrieval_context=[SOURCE_REPORT],
    )

    faithfulness = FaithfulnessMetric(threshold=0.7)
    hallucination = HallucinationMetric(threshold=0.3)

    # We EXPECT this one to score poorly - in a real CI pipeline this test would
    # be written the other way round (asserting it fails), but for a portfolio
    # demo it's shown separately so you can see the metric scores diverge.
    assert_test(test_case, [faithfulness, hallucination])
