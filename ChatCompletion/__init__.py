import logging
import azure.functions as func
import json
import os
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI
import requests #for Azure Search
import httpx

# Load Environment Variables



# Initialize credential and Key Vault client
tenant_id = os.getenv("AZURE_TENANT_ID")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")

key_vault_url = os.getenv("KEYVAULT_URL")
spn_key_vault_url = os.getenv("SPN_KEYVAULT_URL")

credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
kv_client = SecretClient(vault_url=key_vault_url,credential=credential)
spn_kv_client = SecretClient(vault_url=spn_key_vault_url,credential=credential)



# Scope is required to generate the right oauth token. 
# Please check with MLOps platform team if you see any issue
SCOPE = os.getenv("AZURE_BACKEND_SCOPE")

#def token_provider():
#    token = credential.get_token("https://cognitiveservices.azure.com/.default")
#    return token.token

token = credential.get_token(SCOPE).token

# Retrieve secrets from KeyVault using secret names stored in Environment Variables
api_endpoint = kv_client.get_secret(os.getenv("AZURE_OPENAI_ENDPOINT_NAME")).value
api_version = kv_client.get_secret(os.getenv("AZURE_OPENAI_VERSION_NAME")).value
deployment_id = kv_client.get_secret(os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")).value


# Initialize Azure OpenAI client with Entra ID authentication


openai_client = AzureOpenAI(
    base_url=api_endpoint,
    azure_ad_token=token,
    api_version=api_version, #You can use the latest api version
    #make sure you use this to suppress the SSL certificate verification
    http_client = httpx.Client(verify = False)
)



def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing chat completion request.")

    try:
        req_body = req.get_json()
        query = req_body.get("query")

        if not query:
            return func.HttpResponse("Missing 'query' in request body.", status_code=400)
        

        response = openai_client.chat.completions.create(
            model=deployment_id,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": query}
            ]
        )
        reply = response.choices[0].message.content
        return func.HttpResponse(json.dumps({"response": reply}), mimetype="application/json")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(f"Internal Server Error: {str(e)}", status_code=500)
