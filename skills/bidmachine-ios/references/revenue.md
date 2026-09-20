# Revenue Tracking — iOS

Every load and impression event delivers an `AdInfo` to delegate callbacks.

## AdInfo fields

| Field         | Type               | Description                                            |
|---------------|--------------------|--------------------------------------------------------|
| `placementId` | `String`           | Placement ID from the dashboard                        |
| `price`       | `Double`           | eCPM ÷ 1000 (e.g. `0.005` = $5 CPM)                   |
| `precision`   | `RevenuePrecision` | Confidence level of the reported price                 |
| `info`        | `[String: String]` | Raw metadata; known keys: `networkName`, `dsp`, `ecpm` |

## Revenue precision

`RevenuePrecision` is an **`Int`-backed** enum, so `precision.rawValue` is an `Int` (not a `String`) —
type your analytics parameter accordingly, or send the case name via `String(describing:)`.

| Value               | Description                      |
|---------------------|----------------------------------|
| `.exact`            | Real-time auction price          |
| `.estimated`        | Estimated from historical data   |
| `.unknown`          | Precision could not be determined |

## Revenue callback

`didPayRevenue` fires when a billable impression is recorded — forward to analytics.

```swift
func didPayRevenue(adInfo: AdInfo) {
    Analytics.trackRevenue(
        adUnit: adInfo.placementId,
        revenue: adInfo.price,
        precision: adInfo.precision.rawValue,   // Int (RevenuePrecision is Int-backed)
        network: adInfo.info["networkName"]
    )
}
```
