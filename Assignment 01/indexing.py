#-------------------------------------------------------------------------
# AUTHOR: ABHISHEK KANILAL ALHAT
# FILENAME: indexing.py
# SPECIFICATION: This Python script reads textual data from a CSV file and generates a document-term matrix based on
#                TF-IDF (Term Frequency-Inverse Document Frequency) calculations. It preprocesses the text by removing stopwords,
#                such as pronouns and conjunctions, and applies stemming to reduce words to their root forms
#                (e.g., converting "cats" to "cat"). The terms "love," "cat," and "dog" are used as index terms, and their
#                respective TF-IDF scores are calculated for each document. The final output is a matrix, where each row represents a
#                document, and each column contains the TF-IDF score of the corresponding term.

# FOR: CS 5180 - Assignment #1
# TIME SPENT: 20 min
#-----------------------------------------------------------

import csv
from collections import defaultdict
import math

# Load documents from a CSV file
documents = []
with open('collection.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)
    for i, row in enumerate(reader):
        if i > 0:  # Skip the header
            documents.append(row[0])

# Define stopwords and stemming mappings
stopwords = {'i', 'she', 'he', 'they', 'her', 'his', 'their', 'and', 'the', 'a', 'an'}
stemming = {
    'cats': 'cat',
    'loves': 'love',
    'dogs': 'dog'
}

# Function to process a document by removing stopwords and applying stemming
def process_document(document):
    words = document.lower().split()  # Convert to lowercase and split
    processed_words = []
    for word in words:
        if word not in stopwords:  # Filter out stopwords
            processed_words.append(stemming.get(word, word))  # Apply stemming
    return processed_words

# Process all documents
processed_documents = [process_document(document) for document in documents]

# Specify index terms in the order love,cat, dog
index_terms = ['love', 'cat', 'dog']

# Function to compute term frequency (TF)
def compute_tf(term, doc):
    term_frequency = doc.count(term)
    return term_frequency / len(doc) if len(doc) > 0 else 0

# Function to compute inverse document frequency (IDF)
def compute_idf(term, docs):
    num_docs_with_term = sum(1 for doc in docs if term in doc)
    return math.log10(len(docs) / num_docs_with_term) if num_docs_with_term > 0 else 0

# Create the document-term matrix using TF-IDF
doc_term_matrix = []
for doc in processed_documents:
    tfidf_values = []
    for term in index_terms:
        tf = compute_tf(term, doc)
        idf = compute_idf(term, processed_documents)
        tfidf_values.append(tf * idf)
    doc_term_matrix.append(tfidf_values)

# Output the document-term matrix with documents as rows and terms as columns
print(f"{'Document':<{20}}", end="")
for term in index_terms:
    print(f"{term:<{10}}", end="")
print()

# Display each document's TF-IDF values
for i, doc in enumerate(documents):
    print(f"Document{i+1:<{10}}", end="")  # Print Document1, Document2, Document3, etc.
    for tfidf_value in doc_term_matrix[i]:
        print(f"{tfidf_value:<{10}.4f}", end="")
    print()
