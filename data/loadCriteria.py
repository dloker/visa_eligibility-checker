import json
from pymongo import MongoClient

def load_json_to_mongo(file_path, db_name="visa_db", collection_name="visa_requirements"):
    """
    Loads a JSON file into the specified MongoDB collection.
    
    The JSON file is expected to have the structure for the O-1A visa:
    {
        "visa_type": "O-1A",
        "general_info": "General eligibility information...",
        "criteria": [
            {
                "name": "Awards",
                "description": "Detailed info about awards criteria...",
                "scraped_text": "Full scraped text..."
            },
            ... (other criteria)
        ]
    }
    """
    # Connect to the local MongoDB instance
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    collection = db[collection_name]

    # Load the JSON data from file
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Check if the data is a list (multiple documents) or a single document
    if isinstance(data, list):
        result = collection.insert_many(data)
        print(f"Inserted documents with IDs: {result.inserted_ids}")
    elif isinstance(data, dict):
        result = collection.insert_one(data)
        print(f"Inserted document with ID: {result.inserted_id}")
    else:
        print("The JSON structure is not supported. Please provide a dictionary or a list of dictionaries.")

if __name__ == "__main__":
    # Change the path to db.json if necessary
    load_json_to_mongo("O1-A-visa.json")
