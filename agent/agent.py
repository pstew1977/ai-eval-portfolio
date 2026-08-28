"""
A minimal but real multi-step tool-calling agent, using OpenAI's native
function-calling ("tools") API directly - deliberately not using a heavy
agent framework, so every step of the reasoning/tool-call loop is visible
and inspectable, which matters for evaluation.

The agent can call tools more than once per turn (e.g. check knowledge
base, then also check system status) before producing a final answer -
a genuine multi-step agent trajectory, not a single tool call.
"""

import json
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOL_SCHEMAS, TOOL_IMPLEMENTATIONS

load_dotenv()

SYSTEM_PROMPT = (
    "You are an internal IT support agent. You have access to tools to "
    "search documentation, check system status, and create support "
    "tickets. Use tools to investigate before answering - do not guess. "
    "Prefer searching the knowledge base first; check system status if "
    "the user is asking whether something is down right now; only create "
    "a ticket if the other tools don't resolve the issue or the user "
    "explicitly asks you to log one. Keep your final answer concise and "
    "in plain language for a non-technical user."
)


@dataclass
class AgentTrace:
    """Records everything the agent did, for evaluation afterwards."""
    input: str
    final_answer: str = ""
    tool_calls: list = field(default_factory=list)  # list of {name, input_parameters, output}
    raw_messages: list = field(default_factory=list)


def run_agent(user_input: str, max_steps: int = 5) -> AgentTrace:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    trace = AgentTrace(input=user_input)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    for _ in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            tools=TOOL_SCHEMAS,
            temperature=0,
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            # No more tool calls - this is the final answer.
            trace.final_answer = msg.content or ""
            break

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            fn = TOOL_IMPLEMENTATIONS.get(fn_name)

            if fn is None:
                result = f"ERROR: unknown tool '{fn_name}'"
            else:
                result = fn(**fn_args)

            trace.tool_calls.append(
                {"name": fn_name, "input_parameters": fn_args, "output": result}
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                }
            )

    trace.raw_messages = messages
    return trace


if __name__ == "__main__":
    # Quick manual smoke test
    test_input = "Why would our Dataflow Gen2 refresh get stuck?"
    trace = run_agent(test_input)
    print(f"Input: {trace.input}")
    print(f"Tool calls: {[tc['name'] for tc in trace.tool_calls]}")
    print(f"Final answer: {trace.final_answer}")
