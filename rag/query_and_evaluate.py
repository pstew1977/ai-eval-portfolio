"""
Week 3: a small end-to-end RAG pipeline, evaluated with Ragas.

For each question:
  1. Retrieve the most relevant chunks from the Chroma index (build_index.py)
  2. Generate an answer using an LLM, grounded only in those retrieved chunks
  3. Evaluate the result with four Ragas metrics:
       - Faithfulness      : is the answer supported by the retrieved context?
       - Answer Relevancy   : does the answer actually address the question?
       - Context Precision  : are the retrieved chunks actually relevant?
       - Context Recall     : did retrieval find the chunk(s) needed to
                              answer correctly, judged against a reference
                              answer?

Faithfulness/Answer Relevancy tell you about the GENERATION step.
Context Precision/Recall tell you about the RETRIEVAL step.
Together they let you tell whether a bad RAG answer was a retrieval
problem or a generation problem - which matters, because the fix is
completely different (better chunking/embeddings vs. better prompting).

Run with:
    python build_index.py        # once, or whenever documents.py changes
    python query_and_evaluate.py
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from openai import OpenAI

from ragas import evaluate, SingleTurnSample, EvaluationDataset
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
from ragas.llms import LangchainLLMWrapper
from ragas.run_config import RunConfig
from langchain_openai import ChatOpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# Test questions.
# Each has a reference answer - written independently from the docs, the
# way a human SME would answer - used by Context Recall to judge whether
# retrieval found what was actually needed.
# ---------------------------------------------------------------------------
QUESTIONS = [
    {
        "question": "Why would a Dataflow Gen2 refresh get stuck in a queued state?",
        "reference": (
            "It's usually caused by an orphaned job lock left by another "
            "process in the workspace; an admin needs to terminate the "
            "hung process to clear the lock and let the refresh resume."
        ),
    },
    {
        "question": "A guest user can see the report but the data looks empty - why?",
        "reference": (
            "The guest user hasn't been added to the correct Row-Level "
            "Security role in the semantic model using their guest UPN, "
            "even though they have report/app access."
        ),
    },
    {
        "question": "What's the capital of France?",
        "reference": (
            "This is not covered by the internal documentation - the "
            "assistant should say it doesn't know rather than guessing, "
            "since it's outside the scope of the knowledge base."
        ),
    },
]

SYSTEM_PROMPT = (
    "You are an internal support assistant answering questions using ONLY "
    "the context provided below. If the context does not contain the "
    "answer, say clearly that you don't have that information in the "
    "knowledge base - do not guess or use outside knowledge."
)


def retrieve(collection, question: str, k: int = 2):
    results = collection.query(query_texts=[question], n_results=k)
    return results["documents"][0]


def generate(client: OpenAI, question: str, contexts: list[str]) -> str:
    context_block = "\n\n".join(contexts)
    prompt = f"Context:\n{context_block}\n\nQuestion: {question}"
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY not set - see .env.example.")

    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key, model_name="text-embedding-3-small"
    )
    client_chroma = chromadb.PersistentClient(path="./chroma_db")
    collection = client_chroma.get_collection("fabric_kb", embedding_function=embedding_fn)

    openai_client = OpenAI(api_key=api_key)

    samples = []
    print("Running RAG pipeline over test questions...\n")
    for item in QUESTIONS:
        question = item["question"]
        contexts = retrieve(collection, question)
        answer = generate(openai_client, question, contexts)

        print(f"Q: {question}")
        print(f"A: {answer}")
        print(f"Retrieved: {[c[:60] + '...' for c in contexts]}\n")

        samples.append(
            SingleTurnSample(
                user_input=question,
                response=answer,
                retrieved_contexts=contexts,
                reference=item["reference"],
            )
        )

    dataset = EvaluationDataset(samples=samples)

    judge_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4.1-mini", api_key=api_key))

    # Defaults run too many judge calls in parallel with too short a
    # timeout for some connections/API tiers, causing TimeoutErrors and
    # blank (NaN) scores. Lower concurrency + longer timeout trades a
    # slower run for a complete, reliable one - worth it for 3 questions.
    run_config = RunConfig(timeout=180, max_workers=2)

    print("Running Ragas evaluation...\n")
    result = evaluate(
        dataset=dataset,
        metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()],
        llm=judge_llm,
        run_config=run_config,
    )

    print(result)
    df = result.to_pandas()
    df.to_csv("ragas_results.csv", index=False)
    print("\nFull results written to ragas_results.csv")


if __name__ == "__main__":
    main()
