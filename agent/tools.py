"""
Tool definitions for a small IT support agent.

Three tools, deliberately overlapping in plausible-sounding scope so the
agent has to genuinely reason about which one fits a given request -
not just pattern-match on keywords:

  - search_knowledge_base : looks up documented fixes/explanations
    (reuses the same Chroma index built in Week 3's rag/ folder)
  - check_system_status    : checks whether a named system currently has
    a known, active incident
  - create_support_ticket  : escalates to a human when the above two
    can't resolve the request

This mirrors a realistic support-agent shape: try self-serve knowledge
first, check for a known active incident, and only create a ticket if
neither resolves it.
"""

import os
import sys
import json

# Reuse Week 3's Chroma index rather than duplicating it.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag"))

import chromadb
from chromadb.utils import embedding_functions

# ---------------------------------------------------------------------------
# Mock "live system status" data - simulates an incident management API.
# In a real system this would call ServiceNow/PagerDuty/etc.
# ---------------------------------------------------------------------------
ACTIVE_INCIDENTS = {
    "power bi service": None,  # no active incident
    "fabric capacity": "Degraded performance reported in West Europe region since 09:40 - Microsoft investigating (Sev 3).",
    "on-premises gateway": None,
}

# In-memory ticket store for this demo
_TICKETS = []


def search_knowledge_base(query: str, k: int = 2) -> list[str]:
    """Search the Week 3 knowledge base for relevant documentation."""
    api_key = os.environ.get("OPENAI_API_KEY")
    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key, model_name="text-embedding-3-small"
    )
    chroma_path = os.path.join(os.path.dirname(__file__), "..", "rag", "chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection("fabric_kb", embedding_function=embedding_fn)
    results = collection.query(query_texts=[query], n_results=k)
    return results["documents"][0]


def check_system_status(system_name: str) -> str:
    """Check whether a named system has a known active incident."""
    key = system_name.strip().lower()
    incident = ACTIVE_INCIDENTS.get(key)
    if incident:
        return f"ACTIVE INCIDENT for '{system_name}': {incident}"
    if key in ACTIVE_INCIDENTS:
        return f"No active incidents reported for '{system_name}'."
    return f"'{system_name}' is not a recognised system name. Recognised systems: {list(ACTIVE_INCIDENTS.keys())}"


def create_support_ticket(summary: str, priority: str = "Medium") -> str:
    """Create a support ticket for issues that can't be self-resolved."""
    ticket_id = f"TCK-{1000 + len(_TICKETS) + 1}"
    _TICKETS.append({"id": ticket_id, "summary": summary, "priority": priority})
    return f"Ticket {ticket_id} created (priority: {priority}): {summary}"


# ---------------------------------------------------------------------------
# OpenAI function-calling ("tool") schema definitions
# ---------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search internal documentation for known fixes, causes, or "
                "explanations of a technical issue. Use this FIRST for any "
                "question about how something works or why an error might "
                "be happening."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The user's question or issue, in their own words."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_system_status",
            "description": (
                "Check whether a specific named system currently has a "
                "known active incident. Use this when the user is asking "
                "whether a system is currently down or having problems "
                "right now, as opposed to asking how to fix something."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "system_name": {
                        "type": "string",
                        "description": "The system name, e.g. 'Power BI Service', 'Fabric Capacity', 'On-premises gateway'.",
                    }
                },
                "required": ["system_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": (
                "Create a support ticket to escalate to a human. Only use "
                "this if the knowledge base and system status checks did "
                "not resolve the user's issue, or if the user explicitly "
                "asks to log a ticket."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "A short summary of the issue for the ticket."},
                    "priority": {
                        "type": "string",
                        "enum": ["Low", "Medium", "High"],
                        "description": "Ticket priority.",
                    },
                },
                "required": ["summary"],
            },
        },
    },
]

TOOL_IMPLEMENTATIONS = {
    "search_knowledge_base": search_knowledge_base,
    "check_system_status": check_system_status,
    "create_support_ticket": create_support_ticket,
}
