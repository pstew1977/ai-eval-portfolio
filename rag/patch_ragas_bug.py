"""
One-time fix for a known bug in Ragas (as of the version pinned in
requirements.txt): it unconditionally imports a VertexAI integration class
from a path that newer versions of langchain-community removed, which
crashes `import ragas` entirely - even for users who only use OpenAI and
have never touched Google VertexAI.

Upstream issue: https://github.com/vibrantlabsai/ragas/issues/2745
(as of writing, not yet fixed in a released version)

This script patches your installed ragas package to make that import
optional instead of crashing. It's safe to run more than once.

Run this ONCE after `pip install -r requirements.txt`:
    python patch_ragas_bug.py
"""

import importlib.util
import os

# Locate the file WITHOUT importing ragas - importing it is exactly what's
# broken right now, so `import ragas.llms.base` here would just crash with
# the same error we're trying to fix.
spec = importlib.util.find_spec("ragas")
if spec is None or not spec.submodule_search_locations:
    raise SystemExit("Could not locate the installed ragas package.")

ragas_dir = spec.submodule_search_locations[0]
path = os.path.join(ragas_dir, "llms", "base.py")

if not os.path.exists(path):
    raise SystemExit(f"Expected file not found: {path}")

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

already_patched = "ChatVertexAI = None" in content

if already_patched:
    print("Already patched - nothing to do.")
else:
    old_import = (
        "from langchain_community.chat_models.vertexai import ChatVertexAI\n"
        "from langchain_community.llms import VertexAI\n"
    )
    new_import = (
        "try:\n"
        "    from langchain_community.chat_models.vertexai import ChatVertexAI\n"
        "    from langchain_community.llms import VertexAI\n"
        "except ImportError:\n"
        "    ChatVertexAI = None\n"
        "    VertexAI = None\n"
    )

    old_list = """MULTIPLE_COMPLETION_SUPPORTED = [
    OpenAI,
    ChatOpenAI,
    AzureOpenAI,
    AzureChatOpenAI,
    ChatVertexAI,
    VertexAI,
]"""
    new_list = """MULTIPLE_COMPLETION_SUPPORTED = [
    cls
    for cls in [
        OpenAI,
        ChatOpenAI,
        AzureOpenAI,
        AzureChatOpenAI,
        ChatVertexAI,
        VertexAI,
    ]
    if cls is not None
]"""

    if old_import not in content or old_list not in content:
        raise SystemExit(
            "Could not find the expected code to patch - the installed "
            "ragas version may differ from what this script expects. "
            f"File: {path}\n"
            "Check the upstream issue link at the top of this script for "
            "the current status/fix."
        )

    content = content.replace(old_import, new_import)
    content = content.replace(old_list, new_list)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Patched: {path}")

# Verify it actually works now - this import only happens AFTER patching,
# so it's safe even on the first run.
import ragas  # noqa: F401
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall  # noqa: F401

print("Verified: ragas and its metrics import successfully.")
