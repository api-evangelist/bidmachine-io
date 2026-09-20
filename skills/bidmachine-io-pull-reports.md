---
name: Pull SSP, bidder and P2P revenue reports
description: Retrieve BidMachine performance and revenue reports as NDJSON or CSV over a date range, choosing dimensions, inside the documented 45-day window and 6-requests-per-minute limit.
api: openapi/bidmachine-io-reporting-openapi.yml
base_url: https://api-eu.bidmachine.io/api/v1
operations: [retrieveSspReportData, retrieveBidderReportData, retrieveP2pRevenueReportData]
generated: '2026-09-19'
method: generated
source: https://developers.bidmachine.io/api/bidmachine-reporting-api
---

# Pull SSP, bidder and P2P revenue reports

Use this to export BidMachine reporting data for a publisher (SSP) or demand (bidder) account into
a warehouse or spreadsheet. The API is read-only.

## Before you start

- Auth is **HTTP Basic** on every call with the account's dashboard login and password. A 401 carries
  `WWW-Authenticate: Basic realm="Reporting API"`.
- Pick the report:
  - `retrieveSspReportData` — `GET /report/ssp`: publisher performance (impressions, clicks, ctr, ecpm, revenue) by date, country, app, platform, ad_type, demand_partner, payer, placement, coppa.
  - `retrieveBidderReportData` — `GET /report/bidder`: demand-side spend by agency, bidder, seat, adomain, app, country; measures impressions, clicks, ctr, spend, p2p_paas_fee, seller_income.
  - `retrieveP2pRevenueReportData` — `GET /report/p2p-revenue`: payer / demand_partner revenue with estimated_gross_spend, estimated_income, expected_payment, bm_fee. **403** if the account is not entitled.

## Steps

1. **Bound the window.** `start` and `end` are required, `yyyy-MM-dd`; `start` is inclusive and `end`
   is exclusive. Keep `end - start` ≤ **45 days** for SSP and bidder reports (≤ **2 years** for P2P
   revenue). For longer ranges, split into consecutive windows.
2. **Choose the format.** `format=json` streams **NDJSON** (`application/x-ndjson`, one object per
   line); `format=csv` streams CSV, and `csv_header=1` adds the header line (default 0 — no header).
3. **Select fields.** Pass `fields` as a comma-separated list (`style=form`, `explode=false`), e.g.
   `fields=date,country,app_bundle,revenue`. Unknown names return **400** (`{"message": ...}`). Omit
   `fields` for the default column set.
4. **Set a long timeout and pace the calls.** Generation takes 10–60 s and the server timeout is up to
   **300 s**; set the client read timeout ≥ 300 s. The limit is **6 requests per minute** — on **429**
   read the `ad-exchange-warn-message` header ("Please try again in N seconds") and wait; there is no
   `Retry-After`.
5. **Parse line by line** (NDJSON) rather than buffering; the response is the whole window, unpaged.

## Rules

- Never assume a numeric total in the response — sum the rows yourself.
- The contract names only the EU host; the legacy docs used the same `api-eu.bidmachine.io/api/v1/report/ssp` path.
- Reporting is the only surface with a documented rate limit; do not carry the 6/min budget over to
  the Placement Management API or vice versa.
