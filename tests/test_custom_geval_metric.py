"""
Example: building a CUSTOM evaluation metric with G-Eval.

Built-in metrics (faithfulness, relevancy, hallucination) cover the general
case. Real evaluation engineering work often means defining a metric specific
to the business's own quality bar - this is exactly the kind of thing these
AI Evaluation Engineer roles are asking for ("translate business risk and
policy requirements into measurable technical evaluation frameworks").

Here we define a custom metric: "Numeric Accuracy" - does the AI-generated
summary preserve numbers (durations, counts) correctly from the source,
without rounding, dropping, or inventing figures? This matters a lot in a
data/reporting context, where a wrong number in a summary is worse than a
slightly clumsy sentence.

Run with:
    deepeval test run tests/test_custom_geval_metric.py
"""

from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

numeric_accuracy_metric = GEval(
    name="Numeric Accuracy",
    criteria=(
        "Determine whether all numeric facts (durations, counts, dates) in the "
        "'actual output' exactly match the numeric facts stated in the "
        "'context'. Penalise heavily if a number is changed, rounded "
        "differently in a way that loses meaning, or invented. Do not penalise "
        "for numbers from the context that are simply omitted, only for numbers "
        "that are present but wrong."
    ),
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.CONTEXT,
    ],
    threshold=0.7,
)


def test_numeric_accuracy_correct_figures():
    context = [
        "The affected dataflow, along with two dependent dataflows, were stuck "
        "in a queued state for approximately six hours."
    ]
    prompt = "How long was the outage and how many dataflows were affected?"
    ai_output = "The outage lasted around six hours and affected three dataflows in total."

    test_case = LLMTestCase(
        input=prompt,
        actual_output=ai_output,
        context=context,
    )
    assert_test(test_case, [numeric_accuracy_metric])


def test_numeric_accuracy_wrong_figures_should_fail():
    context = [
        "The affected dataflow, along with two dependent dataflows, were stuck "
        "in a queued state for approximately six hours."
    ]
    prompt = "How long was the outage and how many dataflows were affected?"
    # Wrong numbers on purpose: says 2 hours (not 6) and 5 dataflows (not 3)
    ai_output = "The outage lasted around two hours and affected five dataflows in total."

    test_case = LLMTestCase(
        input=prompt,
        actual_output=ai_output,
        context=context,
    )
    assert_test(test_case, [numeric_accuracy_metric])
