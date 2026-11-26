---
doc_id: ge-sp-datastore
title: Set up a Microsoft SharePoint data store
url: https://docs.cloud.google.com/gemini/enterprise/docs/connectors/ms-sharepoint/set-up-data-store
last_updated: 2026-11-10
license: CC BY 4.0 (Google Cloud documentation, attribution required)
collected_at: 2026-11-25
---

This page describes how to create a data store and connect Microsoft SharePoint to Gemini Enterprise.

## Before you begin

Note: To enforce data source access control and secure data in
Gemini Enterprise, ensure that you have
configured your identity provider.

Ensure the following before you set up your Microsoft SharePoint federated
connection:

-

Grant the Discovery Engine Editor role (`roles/discoveryengine.editor`). This role is required for the user to create the data store. To grant this role, do the following:

- In the Google Cloud console, go to the IAM page.

Go to IAM

- Locate the user account and click edit Edit.

- Grant the `Discovery Engine Editor` role to the user. For more information, see IAM roles and permissions.

-
Register Gemini Enterprise as an
OAuth 2.0 application in Microsoft Entra ID
and obtain the following credentials:

-
Client ID

-
Client secret

-
Tenant ID

-
Instance URI

-
Configure the Microsoft API permissions
with the consent of a Microsoft SharePoint admin.

## Create Microsoft SharePoint data store

To create a Microsoft SharePoint data store, do the following:

-
In the Google Cloud console, go to the Gemini Enterprise page.

Gemini Enterprise

-
Select or create a Google Cloud project.

-
In the navigation menu, click Data stores.

-
Click addCreate data store.

-
In the Source section, search for Microsoft SharePoint, and click Select.

-
In the Data section:

-
In the Connector mode section, select Federated search or Data ingestion as the connection mode.

-
Click Continue.

-
In the Authentication settings section, configure authentication based on your chosen connection mode.

- Provide the following authentication details as necessary:

- Client ID: The unique identifier of the application registered in your organization's Microsoft Entra ID.

- Client secret: The secret key generated during the OAuth 2.0 application registration process in Microsoft Entra ID.

- Tenant ID: The unique identifier for your organization in Microsoft Entra admin center.

- Instance URI: The base URL for your Microsoft SharePoint instance (e.g., `https://{your-domain}.sharepoint.com`).

- Microsoft SharePoint Environment Type: Select the environment that hosts your Microsoft 365 tenant:

- Select Standard (the default) if you connect to standard commercial Microsoft 365 or Government Community Cloud (GCC).

- Select US Government if you connect to a Microsoft 365 US Government sovereign cloud (GCC High or DoD).

For more information, see Obtain client credentials.

Note: These settings apply only to Microsoft 365 US Government (sovereign cloud) customers. If you connect to a US Government cloud, use the matching combination; otherwise keep the defaults (Standard and Global):

- GCC: Environment Type Standard, Cloud Environment GCC.

- GCC High: Environment Type US Government, Cloud Environment GCC High.

- DoD: Environment Type US Government, Cloud Environment DoD.

-
If you selected Data ingestion with Federated credentials authentication method, copy the Subject identifier and use it to add federated credential for data ingestion.

- Subject identifier: The unique ID of the service account you plan to use.

-
If you selected Federated search, click Login and complete the third-party sign-in.

-
Click Continue.

-
If you selected Federated search, the Destinations section appears. Enter the base URL for the site.

-
Click Continue.

-
In the Advanced options section, select your Microsoft 365 Cloud Environment:

- If you connect to a Microsoft 365 US Government instance, select the option that matches it: GCC, GCC High, or DoD.

- Otherwise, keep the default, Global.

-
If you selected Federated search, in the Advanced options section, you can refine the scope of your searches and actions by specifying which Microsoft SharePoint sites or specific paths to include or exclude. You can only mutate or retrieve data within the included paths. Requests for out-of-scope data either fail or return no results.

You can add filters to the data store using the Google Cloud console or API:

### Console

Note: When entering multiple sites, separate each URL with a comma. You can also copy and paste a list of URLs directly from a CSV file.

- In the Site filter section:

- Choose the filter type: Include in search or Exclude from search.

- In the Site URL filter field, enter the exact Microsoft SharePoint site URLs to filter, in the format `https://{your-tenant}.sharepoint.com/sites/{your-site-name}`.

Note: Enter the exact site URLs. Subpaths, folders, or document libraries are not supported in this specific field.

- In the Path filter section:

- Choose the filter type: Include in search or Exclude from search.

- In the Path filter field, enter the full SharePoint paths.

Note: This field supports subpaths, folders, and document libraries, in the format, `https://{your-tenant}.sharepoint.com/sites/{your-site-name}/{your-folder-name}/`. Any content under the specified path will be filtered.

### REST

To add filters when creating a data store, call the `setUpDataConnector` method.

`curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: PROJECT_ID" \
"https://ENDPOINT_LOCATION-discoveryengine.googleapis.com/v1alpha/projects/PROJECT_ID/locations/LOCATION:setUpDataConnector" \
-d '{
"collectionId": "COLLECTION_ID",
"collectionDisplayName": "COLLECTION_DISPLAY_NAME",
"dataConnector": {
"dataSource": "sharepoint_federated_search",
"params": {
"client_id": "CLIENT_ID",
"client_secret": "CLIENT_SECRET",
"instance_uri": "INSTANCE_URI",
"tenant_id": "TENANT_ID",
"FILTER_TYPE": {
"FILTER_KEY": [
"FILTER_VALUE1",
"FILTER_VALUE2"
]
}
},
"entities": [
{
"entityName": "file"
}
],
"refreshInterval": "7200s",
"connectorType": "THIRD_PARTY_FEDERATED",
"connectorModes": [
"FEDERATED"
]
}
}'
`

Replace the following:

-
`PROJECT_ID`: the ID of your project.

-
`ENDPOINT_LOCATION`: the multi-region for your API request. Specify one of the following
values:

- `us` for the US multi-region

- `eu` for the EU multi-region

- `global` for the Global location

For more information, see
Specify a multi-region
for your data store.

-
`LOCATION`: the multi-region of your data store:
`global`, `us`, or `eu`

-
`COLLECTION_ID`: the unique ID of the data store.

-
`COLLECTION_DISPLAY_NAME`: the display name of the
data store.

-
`CLIENT_ID`: the client ID for SharePoint
authentication.

-
`CLIENT_SECRET`: the client secret for SharePoint authentication.

-
`INSTANCE_URI`: the instance URI for SharePoint.

-
`TENANT_ID`: the tenant ID for SharePoint.

-
`FILTER_TYPE`: the type of filter added
to your Microsoft SharePoint data stores. For more information, see Filter types.

-
`FILTER_KEY`: the key for the filter, corresponding
to a field in your data. For more information, see Filter keys.

-
`FILTER_VALUES`: the value or values to filter on for
the specified `FILTER_KEY`.

For more details on filter types and adding filters, see Add filters to Microsoft SharePoint data store.

-
Click Continue.

- In the Entities to search (if you selected Federated search) or Entities to sync (if you selected Data ingestion) section:

- Select all the required entities.

- If you selected Federated search, proceed to the next step.

- If you selected Data ingestion, continue with the following steps:

- Optional: To sync specific projects, do the following:

- Click Filter.

- To filter entities out of the index, select the Exclude from the index checkbox, or to ensure that they are included in the index, select the Include to the index checkbox.

- Enter the keys. Press enter after each key.

- Click Save.

- To configure the sync schedule, do the following:

- In the Sync frequency list, select the sync frequency.

- To schedule separate full syncs of entity and identity data, expand the menu in the Full sync section and then select Custom options.

- In the Incremental sync frequency list, select the incremental sync frequency.
For more information, see Sync schedules.

-
Click Continue.

-
In the Actions section:

- If you selected Federated search:

- From Select Microsoft SharePoint actions to enable, select the actions from the category to enable them for the connector.

-
If you selected Data ingestion:

-
In the Authentication settings section, configure authentication based on your chosen connection mode.

-
Provide the following authentication details as necessary:

- Client ID: The unique identifier of the application registered in your organization's Microsoft Entra ID.

- Client Secret: The secret key generated during the OAuth 2.0 application registration process in Microsoft Entra ID.

- Tenant ID: The unique identifier for your organization in Microsoft Entra admin center.

- Instance URI: The base URL for your Microsoft SharePoint instance (e.g., `https://{your-domain}.sharepoint.com`).

For more information, see Obtain client credentials.

-
Click Continue.

-
In the Destinations section, enter the base URL for the site.

-
Click Continue.

-
From Select Microsoft SharePoint actions to enable, select the actions from the category to enable them for the connector.

-
Click Continue.

Note: If you skip adding actions in this step, you can add them later. For more information, see Add actions.

To manage the list of actions, see Manage actions.

Warning:

- Default write actions: When creating and configuring the data store, ensure that any default write actions are explicitly disabled if you only intend to grant read access. Leaving write actions enabled without the corresponding write scopes in Microsoft Entra ID results in authentication and sync errors.

-

If the create data store flow shows an Advanced options section, you can select the Enable Static IP Addresses checkbox within it. This ensures the data store uses a fixed set of IP addresses for outbound traffic, suitable for allowlisting on the source system. For more information, see Configure static IP egress.

-

In the Configuration section:

- From the Multi-region list, select the location for your data connector.

- In the Your data connector name field, enter a name for your connector.

- If you selected `us` or `eu` as the location,
configure the Encryption settings:

- Optional: If you haven't configured single-region keys, click Go to settings page to do so. For more information, see Register a single-region key for third-party connectors.

- Select Google-managed encryption key or Cloud KMS key.

- If you selected Cloud KMS key:

- In the Key management type list, select the appropriate type.

- In the Cloud KMS key list, select the key.

For more information, see Customer-managed encryption keys.

-
Click Continue.

-

In the Billing section, select General pricing or Configurable pricing. For more information, see Verify the billing status of your projects and Licenses.

-
Click Create. Gemini Enterprise creates your data store and displays your data stores on the Data Stores page.

On the Data Stores page, click your data store name to see the status. After the data store state changes from Creating to Active, the Microsoft SharePoint connector is ready to be used.

For an ingestion connector created with Microsoft SharePoint, the data store state transitions from Creating to Running upon synchronization initiation. It then changes to Active once ingestion is complete, signifying that the data store is fully configured. Depending on data volume, ingestion may require several hours.

After creating the data store, create an app, connect it to the Microsoft SharePoint data store, and authorize Gemini Enterprise to access Microsoft SharePoint before executing any queries.

## Enable real-time sync for data ingestion

Preview

— Real-time sync

This feature is

subject to the "Pre-GA Offerings Terms" in the General Service Terms section of the
Service Specific
Terms.

Pre-GA features are available "as is" and might have limited support.

For more information, see the
launch stage descriptions.

Note: Real-time sync is only available for the Data ingestion connection mode.

Real-time sync only syncs document entities and doesn't sync data related to
identity entities. The following table shows which document events are
supported with real-time sync.

| Microsoft SharePoint entities
| Create
| Update
| Delete
| Permission changes

| Attachments
| close
| close
| close
| close

| Comments
| close
| close
| close
| close

| Events
| check
| check
| check
| close

| Files
| check
| check
| check
| close

| Pages
| check
| check
| check
| close

To enable real-time sync for your data store, follow these steps.

-
In the Google Cloud console, go to the Gemini Enterprise page.

Gemini Enterprise

-
In the navigation menu, click Data Stores.

-
Click the name of the Microsoft SharePoint data store for which you want to
enable real-time sync.

-
On the data store Data page, wait until the Connector state changes
to Active.

-
In the Real-time sync field, click View/edit.

-
To enable real-time sync, click the Enable real-time sync toggle.

-
In the Client secret field, enter a value. This value is used to verify
Microsoft SharePoint webhook events. We recommend using a string of 20 characters.

-
Click Save.

Wait for the Real-time sync field to change to Running.

## Data handling and query execution

This section describes how Gemini Enterprise manages your query and the privacy implications of using the federated data store.

### Query execution

After you authorize Microsoft SharePoint and send a search query to Gemini Enterprise:

- Gemini Enterprise sends your search query directly to the Microsoft API.

- Gemini Enterprise blends the results with those from other connected data sources and displays a comprehensive search result.

### Data handling

When using third-party federated search, the following data handling rules apply:

- Your query string is sent to the third-party search backend (Microsoft API).

- These third parties may associate queries with your identity.

- If multiple federated search data sources are enabled, the query might be sent to all of them.

- After the data reaches the third-party system, it is governed by that system's terms of service and privacy policies.

Note: To improve accuracy, an LLM may rewrite your query before it is sent to Microsoft SharePoint. This rewritten query can incorporate information from your session's query history. As a result, parts of your query history might also be included in the query sent to the Microsoft API.

## What's next

- To provide a user interface for querying your Microsoft SharePoint data, create an app and connect it to the Microsoft SharePoint data store.

- To manage the list of actions, see Manage actions.

- To preview how your search results appear after your app is set up, see Get search results.

- To enable alerts for the data store, see Configure alerts for third-party data stores.

- To add filters to the data store, see Add filters to Microsoft SharePoint data store.
