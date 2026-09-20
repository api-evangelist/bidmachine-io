# Error Codes — Android

Every `BidMachineError` returned by the SDK carries a numeric code identifying the failure category. Compare against the constants below to handle specific error types.

## Code Reference

| Code  | Constant              | Description                                           |
|-------|-----------------------|-------------------------------------------------------|
| `100` | `CODE_CONNECTION`     | Can't connect to server.                              |
| `101` | `CODE_BAD_CONTENT`    | Response content is malformed or cannot be parsed.    |
| `102` | `CODE_TIMEOUT`        | Timeout reached.                                      |
| `103` | `CODE_NO_FILL`        | No fill.                                              |
| `104` | `CODE_AD_NOT_READY`   | Ad is not ready to be shown.                          |
| `105` | `CODE_AD_ALREADY_LOADING` | A load is already in progress.                    |
| `106` | `CODE_DESTROYED`      | Ad was destroyed.                                     |
| `107` | `CODE_EXPIRED`        | Ad was expired.                                       |
| `108` | `CODE_INTERNAL`       | Unknown internal error.                               |
| `109` | `CODE_SERVER`         | Server failed to fulfill an apparently valid request. |
| `110` | `CODE_BAD_REQUEST`    | Request contains bad syntax or cannot be fulfilled.   |
| `200` | `CODE_HEADER_BIDDING` | Adapter / header-bidding network error.               |

## Log Format

Single-line description in a unified format:

```text
(<code>) <message>
```

When a `Throwable.cause` is attached and is itself a `BidMachineError`, it is chained on the same line:

```text
(<code>) <message> - (<causeCode>) <causeMessage>
```

Examples:

```text
(100) Can't connect to server
(102) Timeout reached
(103) No fill
(110) Request contains bad syntax or cannot be fulfilled
(108) Unknown internal error - (109) Server failed to fulfill an apparently valid request
```
