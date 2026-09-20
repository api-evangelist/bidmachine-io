---
name: Manage placements on a BidMachine source
description: Authenticate against the BidMachine Placement Management API and list, create, update or delete ad placements on an ad source the publisher owns, without the dashboard.
api: openapi/bidmachine-io-placement-management-openapi.yml
base_url: https://api-eu.bidmachine.io/api/v1
operations: [getAccessToken, listPlacements, createPlacement, updatePlacement, deletePlacement]
generated: '2026-09-19'
method: generated
source: https://developers.bidmachine.io/api/bidmachine-placement-management-api
---

# Manage placements on a BidMachine source

Use this when a publisher wants to script placement setup for an app ("source") instead of
clicking through dashboard.bidmachine.io. Every call is scoped to sources the authenticated
publisher owns; a foreign `sourceId` returns **403**.

## Before you start

- You need the publisher's **dashboard login and password** (the same credentials used at
  https://dashboard.bidmachine.io/sign-in). There are no API keys and no OAuth.
- You need the numeric `sourceId` of the app. It is not listable through this API — read it from the
  dashboard Source page (https://developers.bidmachine.io/dashboard/source).
- There is **no sandbox**. Everything you create is live inventory configuration. There is also no
  undo: `deletePlacement` returns 204 and nothing restores it (see `conventions/bidmachine-io-conventions.yml`, reversibility: none).

## Steps

1. **Get a bearer token** — `getAccessToken`: `POST /auth` with HTTP Basic credentials. The response
   is `{ "token": "...", "expires": "<date-time>" }`. Tokens are short-lived; keep `expires` and
   re-run this step whenever any later call returns **401**.
2. **See what exists** — `listPlacements`: `GET /publisher/sources/{sourceId}/placements` with
   `Authorization: Bearer <token>`. Returns the full array (no pagination). Match on `name` +
   `bundle` before creating, because the placement `id` is derived from those two fields and a
   duplicate returns **409**.
3. **Create** — `createPlacement`: `POST /publisher/sources/{sourceId}/placements` with a
   `PlacementInput` body. Required: `name`, `platform` (`android`|`ios`), `bundle` (Android package
   name, or the numeric App Store id for iOS), `adType` (`banner`|`interstitial`|`rewarded`|`native`),
   `placementType` (`bidding`|`waterfall`), `hva` (boolean). Optional `pricefloor` (USD CPM; omit for
   no floor). **201** returns the placement including its server-generated `id` — store it; the SDK
   and mediation console setup reference it.
4. **Update** — `updatePlacement`: `PUT /publisher/sources/{sourceId}/placements` with the **full**
   `Placement` object including `id`; all fields are replaced, so send unchanged fields too.
   **404** means no placement with that id on that source; **409** means the new name+bundle collides.
5. **Delete** — `deletePlacement`: `DELETE /publisher/sources/{sourceId}/placements/{id}` → **204**,
   no body. Confirm with the user first; it is irreversible.

## Rules

- Errors come back as `{"message": "<text>"}` (not RFC 9457); 401 on the placements path may be an
  HTML "Authentication required" page — treat any 401 as "token expired, go to step 1".
- No idempotency keys exist. Do not retry a `POST` blindly; re-list and reconcile instead.
- No rate limit is documented for this API (the 6/min limit is on the Reporting API).
- Only the EU host (`api-eu.bidmachine.io`) is named by the contract.
