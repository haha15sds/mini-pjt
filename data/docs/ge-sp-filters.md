---
doc_id: ge-sp-filters
title: Add filters to a Microsoft SharePoint data store
url: https://docs.cloud.google.com/gemini/enterprise/docs/connectors/ms-sharepoint/add-filters-to-sharepoint-data-store
last_updated: 2026-11-10
license: CC BY 4.0 (Google Cloud documentation, attribution required)
collected_at: 2026-11-25
---

This page explains how to add filters to your Microsoft SharePoint data stores in
Gemini Enterprise. Filters determine which information is retrieved
or excluded from the Microsoft SharePoint data store when users chat with the Assistant using
the Gemini Enterprise app.

## Permissions impact on filtering

The API permissions you grant during third-party configuration impact how you can filter your Microsoft SharePoint data store:

- Console filtering: To configure filters in the Google Cloud console UI, the `Sites.Selected` scope is required.

- API filtering: If your application uses the `Sites.Read.All` scope, UI filtering is unavailable. You must perform all filtering programmatically using the API.

## Filter types

You can configure the following filters within the `params` object of your data connector:

- Inclusion filter (`admin_filter`): Retrieves only specific information from the
Microsoft SharePoint data store.

- Exclusion filter (`admin_exclusion_filter`): Excludes specific information from the Microsoft SharePoint
data store.

- Legacy filter (`structured_search_filter`): Previously used to create a data store with filters using the API.

## Filter keys

The filter parameters accept an object containing key-value pairs. The keys represent the
SharePoint fields you want to filter on, and the values are arrays of strings
containing the criteria to match. When updating filters using the API, the following keys are supported:

| Filter name
| `FILTER_KEY`
| Description
| URL examples

| Site
| `Site`
| Filters search results and restricts actions to the Microsoft SharePoint site URLs.
| `https://{your-tenant}.sharepoint.com/sites/{your-site-name}`

| Path
| `Path`
| Filters search results and restricts actions to the specific URL prefixes. Use this for granular control to include or exclude sensitive sub-folders. The paths can point to any site, subsite, folder, or file.
| `https://{your-tenant}.sharepoint.com/sites/{your-site-name}/Documents3/`

### Exclude OneDrive content

By default, the Microsoft API returns both SharePoint and OneDrive content.
OneDrive personal content is hosted on a separate domain,
`https://{your-tenant}-my.sharepoint.com`, and every personal site is stored
under the `/personal/` path. To exclude OneDrive content from
Microsoft SharePoint results, add
`https://{your-tenant}-my.sharepoint.com/personal/` as a `Path` exclusion
filter.

### Filter combinations

The following table details how different combinations of inclusion and exclusion filters behave:

| Filter combination
| Behavior

| Path (Inclusion) + Site (Empty)
| Operates as a Path inclusion filter only.

| Site (Inclusion) + Path (Empty)
| Operates as a Site inclusion filter only.

| Site (Inclusion) + Path (Exclusion)
| Includes a broad site while excluding specific granular paths or sensitive folders within it.

| Path (Inclusion) + Site (Inclusion)
| Includes the intersection of both filters. A path is only included if both the path and its parent site are specified. We recommend using a single inclusion filter (Site or Path) to prevent configuration errors due to an empty intersection.

| Site (Exclusion) + Path (Exclusion)
| Excludes any path matching either exclusion filter from the data store.

## Update filters in an existing data store

You can update filters in an existing data store using either the Google Cloud console or the API.

### Console

To modify existing filter configurations:

- In the Google Cloud console navigation menu, click Data stores.

- Select your Microsoft SharePoint data store.

- Click View/edit parameters.

- In the View/edit parameters panel, add or update the Microsoft SharePoint URLs and filter types.

- Click Save.

### REST

To add or to update filters in an existing
Microsoft SharePoint data store, call the
`updateDataConnector`
method with any one of these fields:

- The `admin_filter` field for inclusion filter.

- The `admin_exclusion_filter` field for exclusion filter.

- The legacy `structured_search_filter` field.

Note: For connectors created using the Google Cloud console, we recommend to use the `admin_filter` or `admin_exclusion_filter` parameters for all API updates. The legacy `structured_search_filter` parameter remains supported for existing connectors; you can continue to update it without interruption if your connector was originally configured using that field.

In the request body, the field must contain all the filters you want to have in the data store, including the filters that
are not updated.

To add or update filters in an existing SharePoint data store, run the following
command:

curl -X PATCH

-H "Authorization: Bearer $(gcloud auth print-access-token)"

-H "Content-Type: application/json"

-H "X-Goog-User-Project: PROJECT_ID"

"https://ENDPOINT_LOCATION-discoveryengine.googleapis.com/v1alpha/projects/PROJECT_ID/locations/LOCATION/collections/COLLECTION_ID/dataConnector?updateMask=params"

-d '{
"params": {
"FILTER_TYPE": {
"FILTER_KEY": [
"UPDATED_FILTER_VALUE1",
"UPDATED_FILTER_VALUE2"
]
}
}
}'

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
`COLLECTION_ID`: The ID of the collection
containing the data store.

-
`FILTER_TYPE`: the type of filter added
to your Microsoft SharePoint data stores. For more information, see Filter types.

-
`FILTER_KEY`: the key for the filter,
corresponding to a field in your data. For more information, see Filter keys.

-
`UPDATED_FILTER_VALUES`: the value or values to
filter on for the specified `UPDATED_FILTER_KEY`.

#### Important Considerations

-
If you switch from an inclusion filter to an exclusion filter, or from an exclusion filter to an inclusion filter, you must explicitly remove the filter that is no longer required by setting it to
empty in the request body. For example, if you have an `admin_filter`
and want to switch to `admin_exclusion_filter`, include `"admin_filter": {}` in
addition to `admin_exclusion_filter` in your API request `params` object.
The following example shows `params` object when switching from `admin_filter` to
`admin_exclusion_filter`:

"params": {
"admin_filter": {},
"admin_exclusion_filter": {
"Site": ["https://tenant1.sharepoint.com/sites/hr-portal-site"]
}
}

-
When updating filters, you must include the previously added filters as well. For example, if you have previously added a Site filter and want to update or add a Path filter, use the following command:

"params": {
"admin_filter": {
"Site": ["https://tenant1.sharepoint.com/sites/hr-portal-site"],
"Path": ["https://tenant1.sharepoint.com/sites/site-name1/Documents2"]
}
}

## Verify that the data store includes the filters

You can get the details of the data store to confirm that the filters you added
or updated are correctly applied using the Google Cloud console or the API:

### Console

To view the existing filter configurations:

- In the Google Cloud console > navigation menu, click Data stores.

- Select your Microsoft SharePoint data store.

- Click View/edit parameters.

In the View/edit parameters panel, the existing filters applied to the data store are displayed.

### REST

To verify data store settings, call the
`getDataConnector`
method:

curl -X GET \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "X-Goog-User-Project: PROJECT_ID" \
"https://ENDPOINT_LOCATION-discoveryengine.googleapis.com/v1alpha/projects/PROJECT_ID/locations/LOCATION/collections/COLLECTION_ID/dataConnector"

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
`COLLECTION_ID`: the ID of the collection containing the data store.

In the response, view the `admin_filter`, `admin_exclusion_filter`, or `structured_search_filter` fields in `params` to verify
the filters.

## What's next

- To provide a user interface for querying your Microsoft SharePoint data, create an app and connect it to the Microsoft SharePoint data store.

- To manage the list of actions, see Manage actions.

- To preview how your search results appear after your app is set up, see Get search results.

- To enable alerts for the data store, see Configure alerts for third-party data stores.
