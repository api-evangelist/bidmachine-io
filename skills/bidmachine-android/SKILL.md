---
name: bidmachine-android
description: >
  BidMachine Plus ad SDK integration on Android (Kotlin/Java/Gradle, package
  io.bidmachine.plus). Use this whenever someone is building, debugging, or asking how to
  do anything with BidMachine ads in an Android app: adding the Maven repo and Gradle
  dependency, initializing the SDK in AdNetwork or Mediation mode, showing banner / MREC /
  interstitial / rewarded ads, wiring load, show, reward, and onAdRevenuePaid callbacks,
  reading a BidMachineError code, handling COPPA/GDPR/CCPA consent for kids or
  EU/California users, or slotting BidMachine into an AdMob, MAX, or LevelPlay bidding
  setup via withMediator. Treat any BidMachine-on-Android request as in scope, however
  casually or partially phrased — "how do I…", a pasted error, a half-formed setup
  question. Stay out only when the work actually targets iOS, Unity, or Flutter, or is
  purely server-side OpenRTB bidding or revenue-dashboard reporting — even if those
  mention BidMachine or Android.
license: Apache-2.0
metadata:
  sdk: BidMachine Plus
  platform: android
  source: https://mediation-docs.bidmachine.io/
---

# BidMachine Plus — Android Integration

Integrate the BidMachine Plus Android SDK: **install → initialize → load ads**. All SDK types
live in the `io.bidmachine.plus` package.

## Checklist

You MUST create a task for each of these items and complete them in order — the how-to for each is in
the section below. Items 1–2 come first; items 3–8 follow the answers from item 2 (don't add what
wasn't asked for):

1. **Explore project context & requirements** — files, docs, recent commits, existing ad/monetization setup, and any documented requirements or goals.
2. **Ask clarifying questions** — one at a time; purpose / constraints / success criteria.
3. **Install** — dependency + Maven repo.
4. **Manifest** — INTERNET permission + network-security config.
5. **Initialize** — once at startup, with the chosen demand mode.
6. **Wire ad units** — the requested formats.
7. **Privacy** — regulations for the app's audience.
8. **Verify** — checker + build.

## Requirements

**`minSdk 24`** is required — the SDK is published with `minSdkVersion 24`, so a lower `minSdk`
fails the manifest merger (`uses-sdk:minSdkVersion … cannot be smaller`). Raise the app to 24 if needed.
Gradle 8.7+, Android Gradle Plugin 8.6+, Kotlin 2.1+, Java 17 source/target — treat these as
last-known minimums and confirm the current ones against the docs.

## 1. Explore the project

Before editing, inspect the project and ground the integration in what's already there:

- **Build setup** — module `build.gradle(.kts)`, root `settings.gradle.kts`
  (`dependencyResolutionManagement` centralizes repos), and any `gradle/libs.versions.toml` version
  catalog. Don't assume the app module is `:app`.
- The `AndroidManifest.xml`, the `Application` subclass (or lack of one), and the launcher `Activity`.
- Any existing ad/monetization setup (preserve it — add BidMachine alongside), recent commits, and
  any documented requirements or goals.
- **Language & UI** — Kotlin or Java; Views/XML or Jetpack Compose. Match the project's existing
  conventions; don't introduce a new one. If unclear or mixed, ask in step 2.

## 2. Ask clarifying questions

Ask the essentials — one at a time. You don't have to stall: scaffold what you can and collect the
missing per-app values in a short "what's left to fill" list.

- **App key** (required to run) — a per-app value from the BidMachine dashboard. If it isn't provided
  yet, scaffold with a clearly-marked `YOUR_APP_KEY` `TODO` and report it as the remaining blocker.
  The verifier FAILs on `YOUR_APP_KEY` / `YOUR_PLACEMENT_ID` until replaced. For a **placement ID**,
  use the real value if given, else pass an **empty string** `""` (the default placement) — don't ship
  the literal `YOUR_PLACEMENT_ID`, which is a leftover token the verifier flags.
- **Ad formats** wanted (banner / interstitial / rewarded).
- **Demand mode** — AdNetwork (header bidding; the default) or Mediation.
- **Privacy audience** — child-directed? EU/California users?
- **Language / UI** — only if step 1 left it ambiguous (Kotlin vs Java, Views vs Compose).

## 3. Install

Add the repositories and dependency. For modern projects that centralize repositories in
`settings.gradle.kts` (`dependencyResolutionManagement`), add the `maven` entry there
instead of a module-level `repositories {}` block.

```gradle title="app/build.gradle"
repositories {
    maven { url "https://artifactory.bidmachine.io/bidmachine" }
}

dependencies {
    implementation "io.bidmachine.plus:sdk:0.1.0"                                         // BidMachine Plus SDK
    implementation "com.google.android.gms:play-services-ads-identifier:18.2.0"           // advertising ID
}
```

## 4. Manifest

The SDK needs network access — add the INTERNET permission and reference a network-security config:

```xml title="AndroidManifest.xml"
<manifest>
    <uses-permission android:name="android.permission.INTERNET" />
    <application android:networkSecurityConfig="@xml/network_security_config" />
</manifest>
```

### Network security config

`res/xml/network_security_config.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

## 5. Initialize once at startup

`BidMachine.instance(context, appKey)` returns the SDK instance — **keep a reference** (type
`BidMachine`); you pass it to every ad unit constructor. Call `initialize` once, typically in
`Application.onCreate`.

```kotlin
import io.bidmachine.plus.BidMachine
import io.bidmachine.plus.InitializationConfigBuilder
import io.bidmachine.plus.IntegrationType

val sdk: BidMachine = BidMachine.instance(context, "YOUR_APP_KEY")

val config = InitializationConfigBuilder(IntegrationType.AdNetwork)  // or IntegrationType.Mediation
    .withLoggingEnabled(true)    // remove before release
    .withTestModeEnabled(true)   // remove before release
    .build()

sdk.initialize(config) { status, error ->
    if (error != null) Log.e("BidMachine", "init failed: ${error.message}")
}
```

**`IntegrationType` picks the demand path** (same ad-unit classes either way):

- **`AdNetwork`** — BidMachine is a demand source in an *external* auction: standalone header
  bidding, or feeding a third-party mediation (AdMob / MAX / LevelPlay).
- **`Mediation`** — BidMachine *runs* the auction itself across your demand.

> **`withMediator(...)` is optional and analytics-only.** Add
> `withMediator(MediatorName.ADMOB | MAX | LEVEL_PLAY)` *only* when integrating through an external
> mediation SDK (Google AdMob, AppLovin MAX, ironSource LevelPlay), so BidMachine can report which
> mediator it runs under. Omit it everywhere else — it does nothing, and an integration never
> depends on it.

**Before release:** strip `withLoggingEnabled(true)` and `withTestModeEnabled(true)`.

## 6. Load ads

Create the ad unit with the `sdk` instance + a placement ID, set a listener, `load`, then `show`.
Full lifecycle, callbacks, banner sizes, and publisher extras:
→ [`references/ad-units.md`](references/ad-units.md)

> **`load(activity)` and `show(activity)` take an `Activity`, not a `Context`** — for every ad type.
> `BannerAd`'s *constructor* takes a `Context`, but its `load()` still needs an `Activity`; don't reuse
> the constructor's `Context` to load. Pass `this` from your `Activity` (or keep an `Activity` reference).

All callbacks fire on the **main thread** — safe to touch UI directly. Each callback delivers an
`AdInfo` (placement, price, precision) — see [`references/ad-units.md`](references/ad-units.md).

## Win/loss when inside a mediation waterfall

Ad units expose `notifyWin()` / `notifyLoss(winnerEcpm, networkName)` to report a waterfall round:

```kotlin
ad.notifyWin()                                            // BidMachine won — call before show()
ad.notifyLoss(winnerEcpm = 2.50, networkName = "admob")  // another network won
```

## 7. Privacy

GDPR (IAB TCF v2), CCPA (US Privacy), and GPP signals are read **automatically** from the CMP — no
SDK calls. For child-directed apps call `sdk.regulations.setCoppa(true)`; to suppress user IDs
without the COPPA flag use `setNonPersonalized(true)`. Details →
[`references/privacy.md`](references/privacy.md).

## Troubleshooting — common mistakes

| Symptom | Cause / fix |
|---------|-------------|
| `Could not resolve io.bidmachine.plus:sdk` | Confirm the bidmachine repo is declared and the version matches; the SDK must be resolvable from your configured Maven repos. |
| Ads never load / network errors | Missing `<uses-permission android:name="android.permission.INTERNET" />`. |
| `Unresolved reference: BidMachine` | Using the classic `io.bidmachine:ads.*` SDK. Plus is `io.bidmachine.plus:sdk`, types in `io.bidmachine.plus.*`. |
| `withMediator` "does nothing" | Correct — it is analytics-only, meaningful only with an external mediation SDK (AdMob/MAX/LevelPlay). |
| Test ads / verbose logs in production | Strip `withLoggingEnabled(true)` and `withTestModeEnabled(true)` before release. |

## 8. Verify the integration

Run the bundled read-only checker:

```bash
python3 scripts/verify_integration.py /path/to/android/project
```

It scans the Gradle files, `AndroidManifest.xml`, and Kotlin/Java sources for the dependency,
Maven repos, network-security config, INTERNET permission, the init call, and leftover
test-mode / placeholder keys, printing PASS/WARN/FAIL per check. Then run a debug build to confirm it
compiles — `./gradlew assembleDebug` (or the flavor-specific assemble task you found while exploring;
don't assume the app module is `:app`).

**Stuck on an error?** If a build fails or an API won't resolve and the fix isn't obvious, the
read-only **`bidmachine-android-guide`** agent (when available) diagnoses integration problems against
the official BidMachine documentation — consult it, then apply the fix it points to.

## Deeper topics (load on demand)

| Topic | Reference |
|-------|-----------|
| Ad units — interstitial / rewarded / banner (manual + positioned), AdInfo, callbacks, publisher extras | [`references/ad-units.md`](references/ad-units.md) |
| Privacy & regulations — GDPR/CCPA auto-read, `setCoppa`, `setNonPersonalized` | [`references/privacy.md`](references/privacy.md) |
| Revenue tracking — `onAdRevenuePaid`, precision levels | [`references/revenue.md`](references/revenue.md) |
| Error codes — `BidMachineError` constants and log format | [`references/error-codes.md`](references/error-codes.md) |

## Integration checklist

- [ ] bidmachine Maven repo added
- [ ] `io.bidmachine.plus:sdk` dependency added
- [ ] `play-services-ads-identifier` dependency added
- [ ] `INTERNET` permission + network security config in the manifest, config present in `res/xml/`
- [ ] `BidMachine.initialize` called once at startup; the `BidMachine` instance held
- [ ] `withMediator` added only when integrating through an external mediation SDK (analytics only)
- [ ] `withLoggingEnabled` / `withTestModeEnabled` removed for release builds
- [ ] Ad units `destroy()`-ed in `onDestroy`; full-screen ads reloaded in `onAdClosed`
- [ ] Privacy: `setCoppa` for child-directed apps; GDPR/CCPA left to the CMP auto-read
