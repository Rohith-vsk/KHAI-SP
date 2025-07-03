import logging
import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import ManagedIdentityCredential

# Cosmos DB configuration
cosmos_endpoint = os.getenv("COSMOS_DB_ENDPOINT")
database_name = "TestDb"
container_name = "TestContainer"

# Use managed identity
credential = ManagedIdentityCredential()
client = CosmosClient(cosmos_endpoint, credential=credential)

# Ensure database and container exist
database = client.create_database_if_not_exists(id=database_name, offer_throughput=1000)
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/category")
)

def main(req: func.HttpRequest) -> func.HttpResponse:
    method = req.method
    logging.info(f"Received {method} request.")

    try:
        if method == "POST":
            # Insert sample document
            
            sample_data = req.get_json()
            container.upsert_item(sample_data)
            return func.HttpResponse("Sample document inserted.", status_code=200)

        elif method == "GET":
            # Retrieve sample document
            req_body = req.get_json()
            id = req_body.get("id")
            partition_key_value = req_body.get("category")

            item = container.read_item(item=id, partition_key=partition_key_value)
            return func.HttpResponse(json.dumps(item), mimetype="application/json")

        else:
            return func.HttpResponse("Unsupported HTTP method.", status_code=405)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(f"Internal Server Error: {str(e)}", status_code=500)
