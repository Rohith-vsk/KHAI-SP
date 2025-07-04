import logging
import azure.functions as func
import json
import os
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
import requests #for Azure Search
import httpx

# Load Environment Variables
key_vault_url = os.getenv("KEYVAULT_URL")
spn_key_vault_url = os.getenv("SPN_KEYVAULT_URL")


# Initialize credential and Key Vault client
tenant_id = os.getenv("AZURE_TENANT_ID")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")

credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
kv_client = SecretClient(vault_url=key_vault_url,credential=credential)
spn_kv_client = SecretClient(vault_url=spn_key_vault_url,credential=credential)

# Scope is required to generate the right oauth token. 
# Please check with MLOps platform team if you see any issue
SCOPE = kv_client.get_secret(os.getenv("AZURE_BACKEND_SCOPE")).value


#token = credential.get_token("https://search.azure.com/.default").token

token = credential.get_token(SCOPE).token





# Azure Search config
search_service = kv_client.get_secret(os.getenv("AZURE_SEARCH_SERVICE_NAME")).value
search_index = os.getenv("AZURE_SEARCH_INDEX_NAME")
#search_api_key = kv_client.get_secret(os.getenv("AZURE_SEARCH_API_KEY_NAME")).value


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing AI Search request.")

    try:
        search_query = req.params.get("searchQuery")
        use_search = req.params.get("useSearch")
        

        if not search_query:
            return func.HttpResponse("Missing 'search_query' in request body.", status_code=400)
        
        search_results = None
        if use_search:
            search_results = query_azure_search(search_query, search_service, search_index, token)


        return func.HttpResponse(json.dumps({"search_results": search_results}), mimetype="application/json")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(f"Internal Server Error: {str(e)}", status_code=500)


#Query Azure AI Search


def query_azure_search(query_text: str, search_service: str, index_name: str, token: str):
    url = f"https://{search_service}.search.windows.net/indexes/{index_name}/docs/search?api-version=2023-11-01"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "search": query_text,
        "top": 5
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
