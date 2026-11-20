"""Retrieve from a tiny real in-memory collection, not a hardcoded match."""
from _common import arguments, mp, present, run
from universal_embedder import options


def main():
    args = arguments("Semantic Retriever", "embeddinggemma-2-text-270m.litertlm", text="Where can I borrow books?").parse_args()
    with mp.tasks.retrieval.UniversalEmbedder.create_from_options(options(args)) as embedder:
        dimension = len(embedder.embed_text(args.text).embeddings[0].embedding)
        config = mp.tasks.retrieval.SemanticRetrieverOptions(embedder=embedder, embedding_dimension=dimension)
        with mp.tasks.retrieval.SemanticRetriever.create_from_options(config) as task:
            collection = {"library": "The library lends books to students.", "cafe": "The cafe sells coffee and cake.", "weather": "Tomorrow will be rainy and cold."}
            for key, text in collection.items():
                task.insert_document(doc_id=key, text=text)
            results = task.retrieve(query=args.text, limit=1, min_similarity=0.0)
            if not results:
                raise RuntimeError("No matching record returned.")
            top = results[0]
            return present(args, {"dimension": dimension, "top_match": {"id": top.id, "content": top.content, "score": round(top.score, 5)}}, query=args.text, collection=collection)


if __name__ == "__main__":
    run(main)
