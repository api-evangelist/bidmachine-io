# Ad Units — iOS

All ad unit classes take the SDK instance + a placement ID. Set `delegate`, `load()`,
then `show(from:)` once loaded (check `isLoaded` / `canShow`). Release an ad unit by dropping its
reference and let ARC reclaim it. All delegate callbacks fire on the main thread. On every delegate
only `didLoadAd` and `didFailToLoadAd` are required — the rest are optional.

The `"YOUR_PLACEMENT_ID"` strings below are placeholders for a real dashboard placement. If the user
hasn't provided one, pass an **empty string** `""` (the SDK's default placement) rather than shipping
the literal `YOUR_PLACEMENT_ID` — empty compiles and runs, whereas the placeholder is a leftover token
to be replaced before release.

> **Match the project's UI framework and concurrency style.** The examples below are illustrative
> (UIKit `UIViewController` + delegate). In a SwiftUI app, hold the SDK instance in your `App`/an
> `ObservableObject` and present full-screen ads from the top-most view controller. Callbacks arrive
> on the main thread, so no extra dispatch is needed — follow the project's concurrency style
> (`async/await`, Combine, GCD, or completion handlers). If the style is unclear or mixed, ask first.

## AdInfo

| Property      | Type               | Description                                                  |
|---------------|--------------------|--------------------------------------------------------------|
| `placementId` | `String`           | Placement ID from the dashboard                              |
| `price`       | `Double`           | eCPM ÷ 1000 (e.g. `0.005` = $5 CPM)                         |
| `precision`   | `RevenuePrecision` | `.exact` / `.estimated` / `.unknown`                          |
| `info`        | `[String: String]` | Network metadata. Known keys: `networkName`, `dsp`, `ecpm`  |

`precision`: `.exact` = real-time auction price (trust); `.estimated` = historical approximation;
`.unknown` = undetermined. These three are the only cases of the Plus `RevenuePrecision` enum.

## Interstitial

```swift title="MainViewController.swift"
class MainViewController: UIViewController, InterstitialDelegate {
    private var interstitialAd: InterstitialAd!

    private func createInterstitialAd() {
        interstitialAd = InterstitialAd(sdk, placementId: "YOUR_PLACEMENT_ID")
        interstitialAd.delegate = self
        interstitialAd.load()
    }

    private func showInterstitialAd() {
        if interstitialAd.isLoaded { interstitialAd.show(from: self) }
        else { print("Interstitial ad not ready yet") }
    }

    // The ad unit is released when this object is deallocated (ARC).

    func didLoadAd(adInfo: AdInfo) {
        print("Interstitial loaded from \(adInfo.info["networkName"] ?? "?")")
    }
    func didFailToLoadAd(adInfo: AdInfo?, error: BidMachineError) {
        print("Interstitial load failed: \(error.message)")
    }
    func didShowAd(adInfo: AdInfo) {}
    func didFailToShowAd(adInfo: AdInfo?, error: BidMachineError) {}
    func didClick(adInfo: AdInfo) {}
    func didDismiss(adInfo: AdInfo) { interstitialAd.load() } // reload for next show
    func didExpire(adInfo: AdInfo) {}
    func didPayRevenue(adInfo: AdInfo) {
        print("Interstitial revenue: \(adInfo.price) from \(adInfo.info["networkName"] ?? "?")")
    }
}
```

`InterstitialDelegate`: `didLoadAd`, `didFailToLoadAd`, `didShowAd`, `didFailToShowAd`,
`didClick`, `didDismiss`, `didExpire`, `didPayRevenue`.

## Rewarded

Same as interstitial, plus `didReceiveReward`.

```swift
rewardedAd = RewardedAd(sdk, placementId: "YOUR_PLACEMENT_ID")
rewardedAd.delegate = self
rewardedAd.load()
// show: if rewardedAd.isLoaded { rewardedAd.show(from: self) }

func didReceiveReward(adInfo: AdInfo, reward: Reward?) { /* grant reward; reward?.label, reward?.amount */ }
func didDismiss(adInfo: AdInfo) { rewardedAd.load() } // reload
// didLoadAd / didFailToLoadAd / didShowAd / didFailToShowAd / didClick /
// didExpire / didPayRevenue — same as interstitial
```

`RewardedDelegate` extends `InterstitialDelegate` with `didReceiveReward(adInfo:reward:)` — `reward`
is an optional `Reward` carrying `label` (String) and `amount` (Int).

## Banner

`BannerAd` is a `UIView`. Add it to your own layout, or call `show(at:)` to anchor it to a screen
edge. It is single-shot — it does **not** auto-refresh.

| Size                          | Dimensions | Use case         |
|-------------------------------|------------|------------------|
| `.banner`                     | 320 × 50   | Standard banner  |
| `.leaderboard`                | 728 × 90   | Tablets          |
| `.mrec`                       | 300 × 250  | Medium rectangle |
| `.adaptive(width:maxHeight:)` | custom     | Fluid layout     |

Adaptive height: `BannerAdSize.getMaxAdaptiveHeight(width:)` (`width` / `maxHeight` are `UInt32`).

### Manual banner

```swift title="MainViewController.swift"
class MainViewController: UIViewController, BannerDelegate {
    @IBOutlet private var adContainer: UIView!
    private var bannerAd: BannerAd!

    private func createBannerAd() {
        bannerAd = BannerAd(sdk, placementId: "YOUR_PLACEMENT_ID", size: .banner)
        bannerAd.delegate = self
        bannerAd.load()
    }

    deinit { bannerAd?.removeFromSuperview() }   // detach; ARC reclaims it

    func didLoadAd(adInfo: AdInfo) {
        adContainer.addSubview(bannerAd) // attach only after load
    }
    func didFailToLoadAd(adInfo: AdInfo?, error: BidMachineError) {
        print("Banner load failed: \(error.message)")
    }
    func didShowAd(adInfo: AdInfo) {}
    func didFailToShowAd(adInfo: AdInfo?, error: BidMachineError) {}
    func didClick(adInfo: AdInfo) {}
    func didExpire(adInfo: AdInfo) {}
    func didPayRevenue(adInfo: AdInfo) {}
}
```

`BannerDelegate`: `didLoadAd`, `didFailToLoadAd`, `didShowAd`, `didFailToShowAd`, `didClick`,
`didExpire`, `didPayRevenue`.

### SwiftUI banner

`BannerAd` is a `UIView`, so host it in a `UIViewRepresentable` to place it in a SwiftUI layout. Load
the ad and add it as a subview once `didLoadAd` fires (size the container to the chosen `BannerAdSize`,
e.g. 300×250 for `.mrec`):

```swift
struct BannerView: UIViewRepresentable {
    let sdk: BidMachine
    let placementId: String          // "" for the default placement if none provided

    func makeUIView(context: Context) -> UIView {
        let container = UIView()
        let banner = BannerAd(sdk, placementId: placementId, size: .mrec)
        banner.delegate = context.coordinator
        context.coordinator.banner = banner
        context.coordinator.container = container
        banner.load()
        return container
    }
    func updateUIView(_ uiView: UIView, context: Context) {}
    func makeCoordinator() -> Coordinator { Coordinator() }

    final class Coordinator: NSObject, BannerDelegate {
        var banner: BannerAd?
        weak var container: UIView?
        func didLoadAd(adInfo: AdInfo) {
            guard let banner, let container else { return }
            container.addSubview(banner)         // attach only after load
        }
        func didFailToLoadAd(adInfo: AdInfo?, error: BidMachineError) {
            print("Banner load failed: \(error.message)")
        }
    }
}

// Usage: BannerView(sdk: adManager.sdk, placementId: "").frame(width: 300, height: 250)
```

### Positioned banner

Call `show(at:)` on a loaded banner to anchor it to a screen edge — the SDK resolves the host view
internally (the key window's `rootViewController`, with a top-presented-VC fallback), so no host view
is needed at the call site. `hide()` detaches the view without releasing it.

```swift
// In didLoadAd:
bannerAd.show(at: .horizontalBottom)   // .horizontalTop / .horizontalBottom / .verticalLeft / .verticalRight

// Later:
bannerAd.hide()      // detaches the view; show(at:) can re-display it
// To release: drop the reference (ARC reclaims it).
```

`.verticalLeft` / `.verticalRight` rotate the banner 90° into a side strip (non-adaptive sizes only —
adaptive banners fall back to a horizontal-bottom layout).

## Publisher extras

| Scope         | Where to call         | Applies to                       |
|---------------|-----------------------|----------------------------------|
| **SDK-wide**  | `BidMachine.addExtra` | Every auction from this instance |
| **Per ad unit** | `<AdUnit>.addExtra` | Only that placement's auctions   |

Both the SDK and each ad unit use the same `addExtra(_:forKey:)` signature; a `nil` value removes the
key. Read them back from the `.extras` property (not a `getExtras()` method):

```swift
sdk.addExtra("whale", forKey: "user_segment")
sdk.addExtra(nil, forKey: "ab_bucket")                    // remove
let all: [String: String] = sdk.extras

interstitialAd.addExtra("level_complete", forKey: "placement_context")
let extras: [String: String] = interstitialAd.extras
```
