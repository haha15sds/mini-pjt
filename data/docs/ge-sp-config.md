---
doc_id: ge-sp-config
title: Microsoft SharePoint configuration
url: https://docs.cloud.google.com/gemini/enterprise/docs/connectors/ms-sharepoint/third-party-config
last_updated: 2026-11-18
license: CC BY 4.0 (Google Cloud documentation, attribution required)
collected_at: 2026-11-25
---

To successfully connect Gemini Enterprise with Microsoft SharePoint, you must complete the following configuration steps.

## Set up authentication and permissions

You need to set up authentication and permissions in Microsoft Entra admin center. This is crucial for allowing the connector to access and synchronize data.

### Register Microsoft Entra app for Microsoft SharePoint connector

Before creating the Microsoft SharePoint connector in Gemini Enterprise, register a Microsoft Entra application to enable secure access.

To register Gemini Enterprise as an OAuth 2.0 application in
Entra, do the following:

- Navigate to Microsoft Entra admin center.

- In the navigation menu, expand the Entra ID and select
App registrations.

- On the App registrations page, click addNew registration.

-
On the Register an application page, do the following:

- In the Name field, enter a name for your app.

- In the Supported account types section, select Accounts in this organizational directory only (which may also be labeled Single tenant only or Single tenant only - MSFT depending on your tenant setup). This restricts access to users and guests within your own tenant or directory.

- In the Redirect URI section, do the following:

- In the platform list, select `Web`.

- In the redirect URI field, enter `https://vertexaisearch.cloud.google.com/console/oauth/sharepoint_oauth.html`.

- Click Register. Microsoft Entra creates your app and displays the overview page of your app.

-
In the app navigation menu, click Authentication.

-
Click addAdd redirect URI.

-
In the platform selection pane, do the following:

- Select Web.

- In the Redirect URI field, enter `https://vertexaisearch.cloud.google.com/oauth-redirect`.

- Click Configure.

#### Add federated credential for data ingestion

If you are using Data ingestion as the connection mode and Federated credentials as authentication method, then do the following:

- In the app navigation menu, click Certificates & secrets.

- Select the Federated credentials tab.

- Click addAdd credential.

- Select Other issuer from the Federated credential scenario list.

- In the Issuer field, enter `https://accounts.google.com`.

- In the Subject identifier field, enter the value that you get from the Google Cloud console. This value is generated during the Microsoft SharePoint data store creation in the data section.

- In the Name field, enter a unique label for the federated credential.

- Click Add to grant access.

### Create an OAuth 2.0 configuration

To create a connection using the OAuth 2.0 authentication method, you need to obtain a client ID, client secret, and your Tenant ID from your Microsoft Entra application registration page.

#### Obtain client ID and client secret

-
To obtain the client ID, do the following:

- In the app navigation menu, select Overview.

- Copy the Application (client) ID.

-
To obtain the client secret for the app, do the following:

- In the app navigation menu, select Certificates & secrets.

- Click addNew client secret.

- In the client secret pane, do the following:

- In the Description field, enter a description for the secret.

- In the Expires list, select an expiry duration.

- Click Add.

- Copy the generated client secret string from the Value column, not the UUID in the Secret ID column. Providing the Secret ID causes authentication to fail.

#### Obtain Instance URI

The Instance URI has one of the following formats:

-
For all first-level sites: `https://DOMAIN_OR_SERVER.sharepoint.com`,
for example, `https://example.sharepoint.com`.

-
For a single site: `https://DOMAIN_OR_SERVER.sharepoint.com/sites/WEBSITE`,
for example, `https://example.sharepoint.com/sites/sample-site`.

When you enter the Instance URI, follow these guidelines:

-
Include the `https://` scheme.

-
Use your tenant's canonical SharePoint Online root domain or site
collection URL (ending in `.sharepoint.com`, or `.sharepoint.us` for US
Government clouds) rather than a custom vanity domain such as
`https://intranet.example.com`.

-
Don't include a document library path, folder path, or `.aspx` page URL,
such as `/Shared%20Documents/Forms/AllItems.aspx`.

#### Obtain Tenant ID

Your tenant ID can be found in the Tenant ID box on the overview page in the Microsoft Entra admin center.

### Configure Microsoft API permissions

To configure the required API permissions for the app, do the following:

- Navigate to the app page.

-
In the app navigation menu, select API permissions.

-
Click addAdd permissions.

-
In the Request API permissions pane, select Microsoft Graph.

-
Search for and select the following permissions based on your connection mode:

For the Federated search connection mode, no Graph API permissions are required.

For the Data ingestion connection mode with Federated credentials:

| Permission
| Type
| Description

| `GroupMember.Read.All`
| Application
| Allows the connector to read memberships and basic group properties for all groups without a signed-in user.

| `User.Read`
| Delegated
| Allows the connector to read the profile of signed-in users. It also allows the connector to read basic company information of signed-in users.

| Site control options

| Option 1: `Sites.FullControl.All`
| Application
| Allows the connector to have full control of all site collections.

| Option 2: `Sites.Selected`
| Application
| Allows the connector to access a subset of site collections. The specific site collections and the permissions granted can be configured in SharePoint Online.

| Profile reading options

| Option 1: `User.Read.All`
| Application
| Allows the connector to read user profiles.

| Option 2: `User.ReadBasic.All`
| Application
| Allows the connector to read a basic set of profile properties of other users in the organization.

For the Data ingestion connection mode with OAuth 2.0 refresh token:

| Permission
| Type
| Description

| `GroupMember.Read.All`
| Application
| Allows the connector to read memberships and basic group properties for all groups without a signed-in user.

| `User.Read`
| Delegated
| Allows the connector to read the profile of signed-in users. It also allows the connector to read basic company information of signed-in users.

| `User.Read.All`
| Application
| Allows the connector to read user profiles.

| Site control options

| Option 1: `Sites.FullControl.All`
| Application
| Allows the connector to have full control of all site collections.

| Option 2: `Sites.Selected`
| Application
| Allows the connector to access a subset of site collections. The specific site collections and the permissions granted can be configured in SharePoint Online.

If you enable Actions for either the Federated search or Data ingestion connection mode, also select the following permissions:

| Permission
| Type
| Description

| `Sites.ReadWrite.All`
| Delegated
| Allows the connector to edit or delete documents and list items in all site collections on behalf of the signed-in user.

| `Files.ReadWrite`
| Delegated
| Allows the connector to read (download), create (upload), update, and delete the signed-in user's files.

| `Files.ReadWrite.All`
| Delegated
| Allows the connector to read (download), create (upload), update, and delete all files the signed-in user can access.

| `Sites.Manage.All`
| Delegated
| Allows the connector to create or delete document libraries and lists in all site collections on behalf of the user.

-
Click Add Permissions.

-
In the Request API permissions pane, select Microsoft SharePoint.

-
Search for and select the following permissions based on your connection mode:

For the Federated search connection mode:

| Permission
| Type
| Description

| `Sites.Search.All`
| Delegated
| Allows the connector to run search queries and to read basic site info on behalf of the current signed-in user. Search results are based on the user's permissions instead of the app's permissions.

| `AllSites.Read`
| Delegated
| Allows the connector to read documents and list items in all site collections on behalf of the signed-in user.

For the Data ingestion connection mode with Federated credentials:

| Permission
| Type
| Description

| Site control options

| Option 1: `Sites.FullControl.All`
| Application
| Allows the connector to have full control of all site collections.

| Option 2: `Sites.Selected`
| Application
| Allows the connector to access a subset of site collections with a signed-in user. The specific site collections and the permissions granted can be configured in SharePoint Online.

For the Data ingestion connection mode with OAuth 2.0 refresh token:

| Permission
| Type
| Description

| Site control options

| Option 1: `AllSites.FullControl`
| Delegated
| Allows the connector to have full control of all site collections on behalf of the signed-in user.

| Option 2: `Sites.Selected`
| Delegated
| Allows the connector to access a subset of site collections with a signed-in user. The specific site collections and the permissions granted can be configured in SharePoint Online.

If you enable Actions for either the Federated search or Data ingestion connection mode, also select the following permissions:

| Permission
| Type
| Description

| `AllSites.Write`
| Delegated
| Allows the connector to create, read, update, delete, upload, and download documents and list items in all site collections on behalf of the signed-in user.

-
Click Add Permissions.

Note:
When you use `Sites.Selected`, you must
grant
`fullcontrol` permission to the selected
sites. Additionally, for this permission to take effect, you must do at least one of the
following when creating the SharePoint data store in Gemini Enterprise:

-
Use a specific site URL as your SharePoint connector Instance URI,
for example,
`https://example.sharepoint.com/sites/sample-site`.

-
Provide precise `siteName` filters when setting up the
Gemini Enterprise data store.

-
Grant administrator consent. For information about how to grant consent, see
Grant tenant-wide administrator consent to an
application in the Microsoft Entra documentation.

Caution:

- Tenant-wide administrator consent (CRITICAL): You must grant tenant-wide administrator consent in Microsoft Entra ID for the registered application. Lack of administrator consent is a common failure point that prevents the connector from authenticating.

- Dual App IDs: Note that Gemini Enterprise uses different Microsoft Entra App IDs for different features. You need one App ID for the backend 'Data store' connection and a separate App ID to enable the 'Upload from OneDrive/SharePoint' button in the chat interface. Both applications require administrator consent.

### Grant `fullcontrol` permission to selected sites

If you choose the `Sites.Selected` option to grant control over selected sites
in Microsoft Graph, you must grant the `fullcontrol` permission to
the Gemini Enterprise application. You can do so using one of
the following methods:

- PowerShell

- Microsoft Graph

### PowerShell

For a generic syntax to grant permissions using PnP PowerShell, see
Granting permissions using PnP PowerShell.

-
To grant the `FullControl` permission run the following command in the PowerShell :

`Grant-PnPAzureADAppSitePermission -AppId CLIENT_ID -DisplayName DISPLAY_NAME -Permissions FullControl -Site SITE_URL
`

Replace the following:

- `CLIENT_ID`: the client ID of the Microsoft Entra
application.

- `SITE_URL`: the site URL for your SharePoint site,
for example, `https://example.sharepoint.com/sites/ExampleSite1`.

- `DISPLAY_NAME`: the display name for the Microsoft
Entra application.

### Microsoft Graph

For the overall process to grant permissions using Microsoft Graph, see
Granting permissions using Microsoft Graph.

Use
Microsoft Graph Explorer
to call the following methods. These methods can be called only by a site owner.

-
Get the site ID:

`GET `https://graph.microsoft.com/v1.0/sites/HOSTNAME:SITE_PATH`
`

Replace the following:

- `HOSTNAME`: the Sharepoint site's hostname—for
example, `example.sharepoint.com`.

- `SITE_PATH`: the SharePoint site's path—for example,
`/sites/ExampleSite1` or `/teams/ExampleSite2`.

-
Give `fullcontrol` access to the site whose ID you retrieved in the
previous step.

-
Send the following POST request:

` POST `https://graph.microsoft.com/v1.0/sites/SITE_ID/permissions`
`

-
Use the following request body:

`{
"roles": ["fullControl"],
"grantedToIdentities": [{
"application": {
"id": "CLIENT_ID",
"displayName": "DISPLAY_NAME"
}
}]
}
`

Replace the following:

- `SITE_ID`: the site ID for your SharePoint site
that you received in the previous step. It has the format
`example.sharepoint.com,48332b69-85ab-0000-0000-dbb7132863e7,2d165439-0000-0000-b0fe-030b976868a0`.

- `CLIENT_ID`: the client ID of the Microsoft Entra
application.

- `DISPLAY_NAME`: the display name for the Microsoft
Entra application.

## Troubleshooting

This section describes how to resolve common issues with the Microsoft SharePoint
connector.

### Users see "Need admin approval" when they connect

When users connect to Microsoft SharePoint from the Gemini Enterprise web
app for the first time, Microsoft might show a Need admin approval
screen. This happens if Gemini Enterprise requests administrator-level
permissions, or if your Microsoft Entra tenant prohibits users from authorizing
third-party apps without prior tenant-wide administrator consent.

To resolve this issue, an administrator must complete the first authorization.
After that, other users in your tenant can connect without the approval screen.

-
Ask a Microsoft Entra ID administrator who can grant tenant-wide consent to
sign in to the Gemini Enterprise web app and connect to
Microsoft SharePoint.

-
On the permissions screen, have the administrator select Consent on behalf
of your organization, and then click Accept.

-
Ask users to connect again.

For more information, see
Grant tenant-wide admin consent
in the Microsoft Entra documentation.

Note: Deleting and re-creating the data store doesn't resolve this issue,
because consent is granted in your Microsoft Entra tenant, not to the data store.
