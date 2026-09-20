# Revenue Tracking — Android

Every load and impression event delivers an `AdInfo` object to listener callbacks.

## AdInfo Fields

| Field       | Type                  | Description                                            |
|-------------|-----------------------|--------------------------------------------------------|
| `placementId`  | `String`              | Mediation placement ID from the dashboard                |
| `price`     | `Double`              | eCPM ÷ 1000 (e.g. `0.005` = $5 CPM)                   |
| `precision` | `RevenuePrecision`    | Confidence level of the reported price                 |
| `info`      | `Map<String, String>` | Raw metadata; known keys: `networkName`, `dsp`, `ecpm` |

## Revenue Precision

| Value              | Description                        |
|--------------------|------------------------------------|
| `Exact`            | Real-time auction price            |
| `Estimated`        | Estimated based on historical data |
| `Unknown`          | Precision could not be determined  |

## Revenue Callback

The `onAdRevenuePaid` callback is fired when a billable impression is recorded — use it to forward revenue data to your analytics platform.

```kotlin
override fun onAdRevenuePaid(adInfo: AdInfo) {
    analytics.trackRevenue(
        adUnit = adInfo.placementId,
        revenue = adInfo.price,
        precision = adInfo.precision.name,
        network = adInfo.info["networkName"],
    )
}
```
