# Ad Units — Android

All ad lifecycle callbacks deliver an `AdInfo` describing the winning ad:

| Property      | Type                  | Description                                                  |
|---------------|-----------------------|--------------------------------------------------------------|
| `placementId` | `String`              | Placement ID from the BidMachine dashboard                   |
| `price`       | `Double`              | eCPM ÷ 1000 (e.g. `0.005` = $5 CPM)                          |
| `precision`   | `RevenuePrecision`    | One of `Estimated`, `Exact`, `Unknown`                       |
| `info`        | `Map<String, String>` | Network metadata. Known keys: `networkName`, `dsp`, `ecpm`   |

Read the winning network via `adInfo.info["networkName"]`, and the per-impression revenue via `adInfo.price`.

`adInfo.precision` describes how reliable that price is:

| Value              | Meaning                                                        |
|--------------------|----------------------------------------------------------------|
| `Exact`            | Real-time auction price — trust for reporting                  |
| `Estimated`        | Historical-data estimate — treat as approximate                |
| `Unknown`          | Confidence cannot be determined                                |

All callbacks fire on the main thread, so you can update UI from them directly.

### Interstitial Ads

Full-screen ads. Create once, load, then call `show` when ready. Reload from `onAdClosed` to keep an ad ready for the next show.

```kotlin title="MainActivity.kt"
class MainActivity : AppCompatActivity(), InterstitialListener {
    private lateinit var interstitialAd: InterstitialAd

    private fun createInterstitialAd() {
        interstitialAd = InterstitialAd(sdk, placementId = "YOUR_PLACEMENT_ID")
        interstitialAd.listener = this
        interstitialAd.load(this)
    }

    private fun showInterstitialAd() {
        if (interstitialAd.isLoaded) {
            interstitialAd.show(this)
        } else {
            Log.w("BidMachine", "Interstitial ad not ready yet")
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        interstitialAd.destroy()
    }

    // InterstitialListener callbacks
    override fun onAdLoaded(adInfo: AdInfo) {
        Log.d("BidMachine", "Interstitial loaded from ${adInfo.info["networkName"]}")
    }

    override fun onAdLoadFailed(adInfo: AdInfo?, error: BidMachineError) {
        Log.e("BidMachine", "Interstitial load failed: ${error.message}")
    }

    override fun onAdShown(adInfo: AdInfo) {
        Log.d("BidMachine", "Interstitial displayed")
    }

    override fun onAdShowFailed(adInfo: AdInfo?, error: BidMachineError) {
        Log.e("BidMachine", "Interstitial show failed: ${error.message}")
    }

    override fun onAdClicked(adInfo: AdInfo) {
        Log.d("BidMachine", "Interstitial clicked")
    }

    override fun onAdClosed(adInfo: AdInfo) {
        Log.d("BidMachine", "Interstitial closed")
        interstitialAd.load(this) // reload for next show
    }

    override fun onAdExpired(adInfo: AdInfo) {
        Log.w("BidMachine", "Interstitial expired before show")
    }

    override fun onAdRevenuePaid(adInfo: AdInfo) {
        Log.d("BidMachine", "Interstitial revenue: ${adInfo.price} from ${adInfo.info["networkName"]}")
    }
}
```

| Callback          | Description                          |
|-------------------|--------------------------------------|
| `onAdLoaded`      | Ad loaded and ready to show          |
| `onAdLoadFailed`  | Ad failed to load                    |
| `onAdShown`       | Ad is displayed full-screen          |
| `onAdShowFailed`  | Ad failed to display                 |
| `onAdClicked`     | User tapped the ad                   |
| `onAdClosed`      | User dismissed the ad                |
| `onAdExpired`     | Ad expired before being shown        |
| `onAdRevenuePaid` | Billable impression recorded         |

### Rewarded Ads

Same lifecycle as interstitial, plus an `onAdRewarded` callback when the user completes the ad and earns a reward.

```kotlin title="MainActivity.kt"
class MainActivity : AppCompatActivity(), RewardedListener {
    private lateinit var rewardedAd: RewardedAd

    private fun createRewardedAd() {
        rewardedAd = RewardedAd(sdk, placementId = "YOUR_PLACEMENT_ID")
        rewardedAd.listener = this
        rewardedAd.load(this)
    }

    private fun showRewardedAd() {
        if (rewardedAd.isLoaded) {
            rewardedAd.show(this)
        } else {
            Log.w("BidMachine", "Rewarded ad not ready yet")
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        rewardedAd.destroy()
    }

    // RewardedListener callbacks
    override fun onAdLoaded(adInfo: AdInfo) {
        Log.d("BidMachine", "Rewarded loaded from ${adInfo.info["networkName"]}")
    }

    override fun onAdRewarded(adInfo: AdInfo, reward: Reward?) {
        Log.d("BidMachine", "Reward earned")
        // grant reward to the user
    }

    override fun onAdLoadFailed(adInfo: AdInfo?, error: BidMachineError) {
        Log.e("BidMachine", "Rewarded load failed: ${error.message}")
    }

    override fun onAdShown(adInfo: AdInfo) {}
    override fun onAdShowFailed(adInfo: AdInfo?, error: BidMachineError) {}
    override fun onAdClicked(adInfo: AdInfo) {}

    override fun onAdClosed(adInfo: AdInfo) {
        rewardedAd.load(this) // reload for next show
    }

    override fun onAdExpired(adInfo: AdInfo) {}

    override fun onAdRevenuePaid(adInfo: AdInfo) {
        Log.d("BidMachine", "Rewarded revenue: ${adInfo.price} from ${adInfo.info["networkName"]}")
    }
}
```

| Callback          | Description                          |
|-------------------|--------------------------------------|
| `onAdLoaded`      | Ad loaded and ready to show          |
| `onAdRewarded`    | User completed the ad, grant reward  |
| `onAdLoadFailed`  | Ad failed to load                    |
| `onAdShown`       | Ad is displayed full-screen          |
| `onAdShowFailed`  | Ad failed to display                 |
| `onAdClicked`     | User tapped the ad                   |
| `onAdClosed`      | User dismissed the ad                |
| `onAdExpired`     | Ad expired before being shown        |
| `onAdRevenuePaid` | Billable impression recorded         |

### Banner Ads

`BannerAd` extends `ViewGroup`. Attach it to your own layout, or call `show(position)` to display it at a fixed screen position.

| Size                       | Dimensions | Use case         |
|----------------------------|------------|------------------|
| `Banner`                   | 320 × 50   | Standard banner  |
| `Leaderboard`              | 728 × 90   | Tablets          |
| `MREC`                     | 300 × 250  | Medium rectangle |
| `BannerAdSize.adaptive(width, maxHeight)` | custom | Fluid layout |

> **Tip:** Use `BannerAdSize.getMaxAdaptiveHeight(width)` to calculate `maxHeight` for adaptive banners.

#### Manual Banner

Place a container in your layout that will host the banner view:

```xml title="res/layout/activity_main.xml"
<FrameLayout
    android:id="@+id/ad_container"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_gravity="bottom" />
```

Resolve it once in `onCreate`, then attach the loaded `BannerAd` to it inside `onAdLoaded`:

```kotlin title="MainActivity.kt"
class MainActivity : AppCompatActivity(), BannerListener {
    private lateinit var bannerAd: BannerAd
    private lateinit var adContainer: FrameLayout

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        adContainer = findViewById(R.id.ad_container)
    }

    private fun createBannerAd() {
        bannerAd = BannerAd(this, sdk, placementId = "YOUR_PLACEMENT_ID", size = BannerAdSize.Banner)
        bannerAd.listener = this
        bannerAd.load(this)
    }

    override fun onDestroy() {
        super.onDestroy()
        bannerAd.destroy()
    }

    // BannerListener callbacks
    override fun onAdLoaded(adInfo: AdInfo) {
        Log.d("BidMachine", "Banner loaded from ${adInfo.info["networkName"]}")
        adContainer.addView(bannerAd)
    }

    override fun onAdLoadFailed(adInfo: AdInfo?, error: BidMachineError) {
        Log.e("BidMachine", "Banner load failed: ${error.message}")
    }

    override fun onAdShown(adInfo: AdInfo) {}
    override fun onAdShowFailed(adInfo: AdInfo?, error: BidMachineError) {}
    override fun onAdClicked(adInfo: AdInfo) {}
    override fun onAdExpired(adInfo: AdInfo) {}

    override fun onAdRevenuePaid(adInfo: AdInfo) {
        Log.d("BidMachine", "Banner revenue: ${adInfo.price} from ${adInfo.info["networkName"]}")
    }
}
```

| Callback          | Description                                  |
|-------------------|----------------------------------------------|
| `onAdLoaded`      | Ad loaded and ready to attach to a container |
| `onAdLoadFailed`  | Ad failed to load                            |
| `onAdShown`       | Ad visible on screen, impression tracked     |
| `onAdShowFailed`  | Ad failed to display                         |
| `onAdClicked`     | User tapped the ad                           |
| `onAdExpired`     | Ad expired before being shown                |
| `onAdRevenuePaid` | Billable impression recorded                 |

#### Positioned Banner

`show(position)` and `hide()` are **package-level extension functions** on `BannerAd`, not member
methods — you must import them, or the call fails to compile with `Unresolved reference 'show'`:

```kotlin
import io.bidmachine.plus.show
import io.bidmachine.plus.hide
```

Call `show(position)` on a loaded `BannerAd` to display it at one of the positions below. Call `hide()` to remove it from the screen.

| Position | Constant                          |
|----------|-----------------------------------|
| Top      | `BannerPosition.HorizontalTop`    |
| Bottom   | `BannerPosition.HorizontalBottom` |
| Left     | `BannerPosition.VerticalLeft`     |
| Right    | `BannerPosition.VerticalRight`    |

```kotlin
import io.bidmachine.plus.show   // show(position) / hide() are extensions — see note above
import io.bidmachine.plus.hide

val bannerAd = BannerAd(this, sdk, placementId = "YOUR_PLACEMENT_ID", size = BannerAdSize.Banner)
bannerAd.listener = object : BannerListener {
    override fun onAdLoaded(adInfo: AdInfo) {
        bannerAd.show(BannerPosition.HorizontalBottom) // default position
    }
    override fun onAdLoadFailed(adInfo: AdInfo?, error: BidMachineError) {}
    override fun onAdShown(adInfo: AdInfo) {}
    override fun onAdShowFailed(adInfo: AdInfo?, error: BidMachineError) {}
    override fun onAdClicked(adInfo: AdInfo) {}
    override fun onAdExpired(adInfo: AdInfo) {}
    override fun onAdRevenuePaid(adInfo: AdInfo) {}
}
bannerAd.load(this)

// Later:
bannerAd.hide()    // remove the overlay; show(position) can re-display it
bannerAd.destroy()
```

## Publisher Extras

Attach arbitrary `key → value` pairs forwarded with the bid request as publisher extras. The API exists at two levels with the same shape — choose the one that matches the scope you need.

| Scope             | Where to call            | Applies to                        |
|-------------------|--------------------------|-----------------------------------|
| **SDK-wide**      | `sdk.addExtra`           | Every auction from this instance  |
| **Per ad unit**   | `<AdUnit>.addExtra`      | Only that placement's auctions    |

Passing `null` as the value removes the key. Per-ad-unit extras override SDK-wide values for the same key on that placement.

### SDK-wide

```kotlin
val sdk = BidMachine.instance(context, "YOUR_APP_KEY")

sdk.addExtra("user_segment", "whale")
sdk.addExtra("ab_bucket", "control")

val all: Map<String, String> = sdk.extras
sdk.addExtra("ab_bucket", null) // remove
```

### Per ad unit

Available on `BannerAd`, `InterstitialAd`, and `RewardedAd`:

```kotlin
interstitialAd.addExtra("placement_context", "level_complete")
bannerAd.addExtra("screen", "main_menu")

val extras: Map<String, String> = interstitialAd.extras
```
