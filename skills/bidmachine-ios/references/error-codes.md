# Error Codes — iOS

The SDK returns errors as `BidMachineError` (Swift) / `BMError` (Obj-C), an `NSError` subclass. Two
things are public: `error.code` (the numeric category, `Int`) and `error.message` (a `String`).
Switch on `error.code` against the numbers below.

> **Named code constants are not part of the public API.** The backing `Code` enum is internal, and
> there are no `BMErrorCode*` Obj-C constants — only the raw `error.code` number and `error.message`
> string are exposed. The internal case names below are for orientation only; switch on the number.

| Code  | Internal name    | Description                                           |
|-------|------------------|-------------------------------------------------------|
| `100` | `connection`     | Can't connect to server.                              |
| `101` | `badContent`     | Response content is malformed or cannot be parsed.    |
| `102` | `timeout`        | Timeout reached.                                      |
| `103` | `noFill`         | No fill.                                              |
| `104` | `adNotReady`     | Ad is not ready to be shown.                          |
| `105` | `alreadyLoading` | A load is already in progress.                        |
| `106` | `destroyed`      | Ad was destroyed.                                     |
| `107` | `expired`        | Ad was expired.                                       |
| `108` | `internal`       | Unknown internal error.                               |
| `109` | `server`         | Server failed to fulfill an apparently valid request. |
| `110` | `badRequest`     | Request contains bad syntax or cannot be fulfilled.   |
| `200` | `headerBidding`  | Adapter / header-bidding network error.               |

## Handling errors

Switch on the raw `error.code`:

```swift
func didFailToLoadAd(adInfo: AdInfo?, error: BidMachineError) {
    switch error.code {
    case 103: print("No fill")
    case 102: print("Timed out")
    default:  print("Load failed (\(error.code)): \(error.message)")
    }
}
```

iOS does not expose a public log formatter or a `cause` property — read `error.message` directly;
an underlying `NSError` may be attached via `NSUnderlyingErrorKey`.

## Common triage

- **No fill (103)** — expected intermittently; verify app key, placement ID, test mode.
- **Connection / timeout (100 / 102)** — connectivity; check ATS (`NSAllowsArbitraryLoads`).
- **Header bidding (200)** — an adapter / header-bidding network in the external mediation failed;
  check that mediation SDK and its BidMachine adapter, not the analytics-only `with(mediator:)` label.
- **Bad request (110)** — usually a bad placement ID or app key.
