#!/bin/bash

# === CONFIGURATION ===
SP_NAME="my-functionapp-sp"
SUBSCRIPTION_ID="<your-subscription-id>"
RESOURCE_GROUP="<your-resource-group>"
KEYVAULT_NAME="<your-keyvault-name>"
OPENAI_ACCOUNT_NAME="<your-openai-account-name>"
SEARCH_SERVICE_NAME="<your-search-service-name>"

# === CREATE SERVICE PRINCIPAL ===
echo "Creating Service Principal..."
SP_OUTPUT=$(az ad sp create-for-rbac --name "$SP_NAME" --role contributor --scopes /subscriptions/$SUBSCRIPTION_ID --sdk-auth)
APP_ID=$(echo $SP_OUTPUT | jq -r '.clientId')
CLIENT_SECRET=$(echo $SP_OUTPUT | jq -r '.clientSecret')
TENANT_ID=$(echo $SP_OUTPUT | jq -r '.tenantId')

echo "Service Principal created:"
echo "  Client ID: $APP_ID"
echo "  Tenant ID: $TENANT_ID"

# === ASSIGN ACCESS TO KEY VAULT ===
echo "Assigning Key Vault access..."
az keyvault set-policy --name $KEYVAULT_NAME --spn $APP_ID --secret-permissions get list

# === ASSIGN ACCESS TO AZURE OPENAI ===
echo "Assigning Azure OpenAI access..."
az role assignment create --assignee $APP_ID \
  --role "Cognitive Services OpenAI User" \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$OPENAI_ACCOUNT_NAME

# === ASSIGN ACCESS TO AZURE AI SEARCH ===
echo "Assigning Azure AI Search access..."
az role assignment create --assignee $APP_ID \
  --role "Search Index Data Reader" \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Search/searchServices/$SEARCH_SERVICE_NAME

# === OUTPUT ENVIRONMENT VARIABLES ===
echo ""
echo "=== Environment Variables for Azure Function App ==="
echo "AZURE_CLIENT_ID=$APP_ID"
echo "AZURE_CLIENT_SECRET=$CLIENT_SECRET"
echo "AZURE_TENANT_ID=$TENANT_ID"
echo "KEYVAULT_URL=https://$KEYVAULT_NAME.vault.azure.net/"
