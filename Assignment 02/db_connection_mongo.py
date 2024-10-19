from pymongo import MongoClient
import string

# Connect to the MongoDB database
def connectDataBase():
    client = MongoClient('mongodb://localhost:27017/')  # Connect to MongoDB
    db = client["documentDB"]  # Create or use 'documentDB'
    return db

# Create a document in the collection
def createDocument(col, docId, docText, docTitle, docDate, docCat):
    document = {
        "_id": int(docId),
        "text": docText.lower().split(),
        "title": docTitle,
        "date": docDate,
        "category": docCat
    }
    try:
        col.insert_one(document)
        print(f"Document with ID {docId} created successfully.")
    except Exception as e:
        print(f"Error: {e}")

# Update a document
def updateDocument(col, docId, docText, docTitle, docDate, docCat):
    new_data = {
        "$set": {
            "text": docText.lower().split(),
            "title": docTitle,
            "date": docDate,
            "category": docCat
        }
    }
    result = col.update_one({"_id": int(docId)}, new_data)
    if result.matched_count > 0:
        print(f"Document with ID {docId} updated successfully.")
    else:
        print(f"No document found with ID {docId}.")

# Delete a document
def deleteDocument(col, docId):
    result = col.delete_one({"_id": int(docId)})
    if result.deleted_count > 0:
        print(f"Document with ID {docId} deleted successfully.")
    else:
        print(f"No document found with ID {docId}.")

# Generate an inverted index
def getIndex(col):
    index = {}
    documents = col.find()  # Retrieve all documents

    # Build the inverted index
    for doc in documents:
        title = doc["title"]
        for term in doc["text"]:
            # Strip punctuation from the term (e.g., "here." -> "here")
            cleaned_term = term.strip(string.punctuation)

            if cleaned_term not in index:
                index[cleaned_term] = f"{title}:1"
            else:
                entries = index[cleaned_term].split(", ")

                updated_entries = []
                term_found = False

                # Iterate through existing entries to update or add new ones
                for entry in entries:
                    entry_title, entry_count = entry.split(":")
                    if entry_title == title:
                        # Increment the count if the title already exists for the term
                        updated_entries.append(f"{title}:{int(entry_count) + 1}")
                        term_found = True
                    else:
                        updated_entries.append(entry)

                # Add a new entry if the term doesn't exist for this title
                if not term_found:
                    updated_entries.append(f"{title}:1")

                # Sort entries alphabetically by title for consistent output
                updated_entries.sort()

                # Join the updated entries into a single string
                index[cleaned_term] = ", ".join(updated_entries)

    # Return the index ordered by term
    return dict(sorted(index.items()))

