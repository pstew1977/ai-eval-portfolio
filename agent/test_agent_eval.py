"""
Week 4: evaluating an AI AGENT, not just a single LLM call.

This is a different evaluation problem from Weeks 1-3. Those checked
"is this one output good?" - this checks "did the agent take the RIGHT
SEQUENCE OF ACTIONS to solve the problem?" A wrong tool call, a missed
tool call, or wrong arguments can all produce a plausible-sounding final
answer while still being a failure - which is exactly what makes agent
evaluation harder than plain LLM evaluation, and exactly why job specs
increasingly call it out as a distinct skill from "AI evaluation" in
general.

Three metrics used here, each checking a different failure mode:

  - ToolCorrectnessMetric     : did the agent call the RIGHT tools
                                 (regardless of arguments/outcome)?
  - ArgumentCorrectnessMetric  : were the ARGUMENTS to those tools correct?
  - TaskCompletionMetric       : did the agent actually SOLVE the task,
                                 end to end?

Run with:
    deepeval test run test_agent_eval.py
"""

from deepeval import assert_test
from deepeval.metrics import (
    ToolCorrectnessMetric,
    ArgumentCorrectnessMetric,
    TaskCompletionMetric,
)
from deepeval.test_case import LLMTestCase, ToolCall

from agent import run_agent

# All tools the agent has access to - passing this to ToolCorrectnessMetric
# lets it evaluate tool SELECTION properly: not just "were the expected
# tools called" but "were any OTHER, unnecessary tools also called
# alongside them". Without this, a passing agent could call an extra,
# irrelevant tool and still score 1.0, as long as it also hit the
# expected one - a real gap caught when first reviewing these results.
AVAILABLE_TOOLS = [
    ToolCall(name="search_knowledge_base"),
    ToolCall(name="check_system_status"),
    ToolCall(name="create_support_ticket"),
]


def _trace_to_test_case(trace, expected_tool_names: list[str], task: str = None) -> LLMTestCase:
    """Convert an AgentTrace into the ToolCall/LLMTestCase shapes DeepEval expects."""
    tools_called = [
        ToolCall(
            name=tc["name"],
            input_parameters=tc["input_parameters"],
            output=tc["output"],
        )
        for tc in trace.tool_calls
    ]
    expected_tools = [ToolCall(name=name) for name in expected_tool_names]

    return LLMTestCase(
        input=trace.input,
        actual_output=trace.final_answer,
        tools_called=tools_called,
        expected_tools=expected_tools,
    )


# ---------------------------------------------------------------------------
# Case 1: a "how does this work" question -> should use the knowledge base,
# NOT check system status or create a ticket.
# ---------------------------------------------------------------------------
def test_knowledge_question_uses_kb_only():
    trace = run_agent("Why would our Dataflow Gen2 refresh get stuck in a queued state?")
    test_case = _trace_to_test_case(trace, expected_tool_names=["search_knowledge_base"])

    tool_correctness = ToolCorrectnessMetric(available_tools=AVAILABLE_TOOLS, should_consider_ordering=False)
    argument_correctness = ArgumentCorrectnessMetric()
    task_completion = TaskCompletionMetric(
        task="Explain to the user why their Dataflow Gen2 refresh might be stuck."
    )

    assert_test(test_case, [tool_correctness, argument_correctness, task_completion])


# ---------------------------------------------------------------------------
# Case 2: a "is X down right now" question -> should check system status,
# NOT just search static documentation.
# ---------------------------------------------------------------------------
def test_status_question_checks_live_status():
    trace = run_agent("Is Fabric Capacity down right now? Users are reporting slow reports.")
    test_case = _trace_to_test_case(trace, expected_tool_names=["check_system_status"])

    tool_correctness = ToolCorrectnessMetric(available_tools=AVAILABLE_TOOLS, should_consider_ordering=False)
    argument_correctness = ArgumentCorrectnessMetric()
    task_completion = TaskCompletionMetric(
        task="Tell the user whether Fabric Capacity currently has a known active incident."
    )

    assert_test(test_case, [tool_correctness, argument_correctness, task_completion])


# ---------------------------------------------------------------------------
# Case 3: a multi-step case - user has already checked docs and status
# themselves and explicitly asks to escalate. Correct behaviour is to
# create a ticket, not re-search the knowledge base pointlessly.
# ---------------------------------------------------------------------------
def test_explicit_escalation_creates_ticket():
    trace = run_agent(
        "I already checked the docs and the status page, Fabric Capacity looks fine "
        "but my reports are still failing to refresh. Please just log a ticket for me."
    )
    test_case = _trace_to_test_case(trace, expected_tool_names=["create_support_ticket"])

    tool_correctness = ToolCorrectnessMetric(available_tools=AVAILABLE_TOOLS, should_consider_ordering=False)
    task_completion = TaskCompletionMetric(
        task="Escalate the user's unresolved issue by creating a support ticket, as they explicitly requested."
    )

    assert_test(test_case, [tool_correctness, task_completion])


# ---------------------------------------------------------------------------
# Case 4 (the trap): a question with NO relevant tool at all. A good agent
# should recognise this and NOT call any tool, or should push back rather
# than fabricate a tool call. Tests over-eager tool use, not just
# under-use.
# ---------------------------------------------------------------------------
def test_irrelevant_question_does_not_force_a_tool_call():
    trace = run_agent("What's a good name for a pet goldfish?")
    test_case = _trace_to_test_case(trace, expected_tool_names=[])

    tool_correctness = ToolCorrectnessMetric(available_tools=AVAILABLE_TOOLS, should_consider_ordering=False)
    assert_test(test_case, [tool_correctness])
