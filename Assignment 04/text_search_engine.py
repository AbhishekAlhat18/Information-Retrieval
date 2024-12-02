import re
import math
from pymongo import MongoClient
from typing import List, Dict, Any


class TextSearchEngine:
    def __init__(self):
        # Establish connection with MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['search_database']

        # Drop any existing collections to start fresh
        self.db['terms_collection'].drop()
        self.db['documents_collection'].drop()

        # Initialize collections
        self.terms_collection = self.db['terms_collection']
        self.documents_collection = self.db['documents_collection']

        # Sample documents for indexing
        self.docs = [
            "After the medication, headache and nausea were reported by the patient.",
            "The patient reported nausea and dizziness caused by the medication.",
            "Headache and dizziness are common effects of this medication.",
            "The medication caused a headache and nausea, but no dizziness was reported."
        ]

        # Store terms' vocabulary and their positions
        self.vocabulary = {}

    def preprocess(self, text: str) -> List[str]:
        """Process text by removing punctuation and converting to lowercase"""
        text = re.sub(r'[^\w\s]', '', text.lower())  # Remove non-alphanumeric characters
        return text.split()

    def create_ngrams(self, tokens: List[str]) -> List[str]:
        """Create unigrams, bigrams, and trigrams"""
        ngrams = tokens.copy()

        # Generate bigrams
        bigrams = [f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)]

        # Generate trigrams
        trigrams = [f"{tokens[i]} {tokens[i + 1]} {tokens[i + 2]}" for i in range(len(tokens) - 2)]

        return ngrams + bigrams + trigrams

    def build_inverted_index(self):
        """Build inverted index with TF-IDF values"""
        term_doc_count = {}

        # Pass 1: Count document frequencies
        for doc_id, doc_content in enumerate(self.docs, 1):
            tokens = self.preprocess(doc_content)
            ngrams = self.create_ngrams(tokens)

            unique_terms = set(ngrams)
            for term in unique_terms:
                if term not in term_doc_count:
                    term_doc_count[term] = 0
                term_doc_count[term] += 1

        # Pass 2: Store terms and their TF-IDF values in MongoDB
        for doc_id, doc_content in enumerate(self.docs, 1):
            tokens = self.preprocess(doc_content)
            ngrams = self.create_ngrams(tokens)

            term_freq = {}
            for term in ngrams:
                term_freq[term] = term_freq.get(term, 0) + 1

            # Insert document into MongoDB
            self.documents_collection.insert_one({
                '_id': doc_id,
                'content': doc_content
            })

            # Calculate TF-IDF and update the terms collection
            for term, freq in term_freq.items():
                tf = 1 + math.log(freq)  # Term Frequency
                idf = math.log(len(self.docs) / (term_doc_count[term] + 1)) + 1  # Inverse Document Frequency
                tfidf = tf * idf  # TF-IDF calculation

                if term not in self.vocabulary:
                    self.vocabulary[term] = len(self.vocabulary)

                # Add term to the inverted index in MongoDB
                self.terms_collection.update_one(
                    {'_id': term},
                    {'$addToSet': {'docs': {
                        'doc_id': doc_id,
                        'tf_idf': tfidf,
                        'pos': self.vocabulary[term]
                    }}},
                    upsert=True
                )

    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search documents using vector space model"""
        query_tokens = self.preprocess(query)
        query_ngrams = self.create_ngrams(query_tokens)

        # Retrieve relevant document IDs based on query terms
        matching_doc_ids = set()
        for term in query_ngrams:
            term_data = self.terms_collection.find_one({'_id': term})
            if term_data:
                matching_doc_ids.update(doc['doc_id'] for doc in term_data.get('docs', []))

        # Calculate similarity scores for the matching documents
        search_results = []
        for doc_id in matching_doc_ids:
            doc = self.documents_collection.find_one({'_id': doc_id})

            doc_vector = {}
            doc_tokens = self.preprocess(doc['content'])
            doc_ngrams = self.create_ngrams(doc_tokens)

            # Get TF-IDF values for the document terms
            for term in set(doc_ngrams):
                term_data = self.terms_collection.find_one({'_id': term})
                if term_data:
                    for doc_term in term_data.get('docs', []):
                        if doc_term['doc_id'] == doc_id:
                            doc_vector[term] = doc_term['tf_idf']
                            break

            # Query vector
            query_vector = {}
            for term in query_ngrams:
                term_data = self.terms_collection.find_one({'_id': term})
                if term_data:
                    query_vector[term] = 1.0  # Represent each term in query as 1.0

            # Calculate cosine similarity
            numerator = sum(query_vector.get(term, 0) * doc_vector.get(term, 0) for term in set(list(query_vector.keys()) + list(doc_vector.keys())))

            query_norm = math.sqrt(sum(1 ** 2 for _ in query_vector))
            doc_norm = math.sqrt(sum(v ** 2 for v in doc_vector.values()))

            if query_norm * doc_norm > 0:
                cosine_similarity = numerator / (query_norm * doc_norm)
                search_results.append({
                    'content': doc['content'],
                    'score': round(cosine_similarity, 2)
                })

        # Sort results by score in descending order
        return sorted(search_results, key=lambda x: x['score'], reverse=True)

    def execute_queries(self, queries: List[str]):
        """Execute queries and display results"""
        for query in queries:
            print(f"Query: {query}")
            results = self.search_documents(query)
            for result in results:
                print(f'"{result["content"]}", {result["score"]}')
            print()


def main():
    # Initialize the search engine
    engine = TextSearchEngine()

    # Build the index for documents
    engine.build_inverted_index()

    # Sample queries
    queries = [
        "nausea and dizziness",
        "effects",
        "nausea was reported",
        "dizziness",
        "the medication"
    ]

    # Execute queries and display results
    engine.execute_queries(queries)


if __name__ == "__main__":
    main()
