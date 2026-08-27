"""
A small, realistic "internal documentation" set for a Fabric/Power BI
platform knowledge base - the kind of thing a support/ops team would
actually query. Each entry is a short, self-contained doc chunk.

Kept deliberately small (6 docs) so the whole pipeline runs in seconds
and is easy to read end-to-end - a real system would have thousands of
chunks, but the evaluation approach is identical at any scale.
"""

DOCS = [
    {
        "id": "doc1",
        "title": "Dataflow Gen2 stuck jobs",
        "text": (
            "If a Dataflow Gen2 refresh appears stuck in a queued or in-progress "
            "state for longer than 30 minutes, the most common cause is an "
            "orphaned job lock left behind by a separate process in the same "
            "workspace that did not release its lock cleanly. To resolve this, "
            "an admin should identify and manually terminate the hung process "
            "in the workspace, which clears the lock and allows queued refreshes "
            "to resume automatically. Dependent dataflows that were blocked will "
            "typically recover without further action once the lock is cleared."
        ),
    },
    {
        "id": "doc2",
        "title": "Power BI Row-Level Security for external users",
        "text": (
            "External (guest) users accessing a Power BI report via B2B "
            "guest access must be explicitly added to the relevant RLS role "
            "in the semantic model, using their guest UPN (which typically "
            "includes '#EXT#' in the domain portion). Simply granting "
            "workspace or app access is not sufficient - if a guest user is "
            "not mapped to an RLS role, they will see an empty report rather "
            "than an access-denied error, which is a common source of "
            "confusion when troubleshooting."
        ),
    },
    {
        "id": "doc3",
        "title": "Fabric capacity throttling",
        "text": (
            "Fabric capacity throttling occurs when sustained compute usage "
            "(measured in Capacity Units) exceeds the capacity's available "
            "headroom over a rolling window. When throttling begins, "
            "interactive operations such as report rendering are delayed "
            "first; if usage remains high, background operations such as "
            "scheduled refreshes are delayed next. Throttling is visible in "
            "the Fabric Capacity Metrics app, and typically resolves on its "
            "own once usage drops, though sustained overuse may require "
            "moving workloads to a larger capacity SKU."
        ),
    },
    {
        "id": "doc4",
        "title": "Gateway permissions for on-premises data sources",
        "text": (
            "When a Dataflow Gen2 or dataset uses an on-premises data source "
            "via an on-premises data gateway, each individual data source "
            "connection within the gateway must have the relevant user or "
            "service account explicitly granted 'Users' or 'Admins' "
            "permission. Granting access to the gateway itself does not "
            "automatically grant access to every data source configured "
            "within it - each data source's permissions are managed "
            "separately in the gateway's configuration."
        ),
    },
    {
        "id": "doc5",
        "title": "Direct Lake semantic models",
        "text": (
            "Direct Lake mode allows a Power BI semantic model to query "
            "data directly from OneLake Delta tables without a separate "
            "import or DirectQuery step, giving import-like performance "
            "without a scheduled refresh. If query performance degrades "
            "unexpectedly, a common cause is 'fallback to DirectQuery', "
            "which Fabric triggers automatically when a query cannot be "
            "satisfied directly from OneLake (for example, due to certain "
            "unsupported DAX functions or excessive table size); this "
            "fallback is visible in Performance Analyzer traces."
        ),
    },
    {
        "id": "doc6",
        "title": "Staging table growth and refresh latency",
        "text": (
            "Gradual, ongoing increases in report or dashboard refresh "
            "latency over a period of days or weeks - rather than a sudden "
            "spike - are frequently caused by unbounded growth in a staging "
            "or intermediate table, where a scheduled cleanup or archival "
            "step has stopped running or was never configured. Reviewing "
            "row counts for staging tables over time, and confirming "
            "nightly cleanup jobs are completing successfully, should be an "
            "early step when investigating this pattern."
        ),
    },
]
