---
name: bidmachine-ios
description: >
  Use this skill for any task involving the BidMachine (BidMachine Plus) ad SDK in an iOS
  app — Swift or Objective-C, CocoaPods or Swift Package Manager. Trigger it whenever
  someone wants to add, set up, start, integrate, configure, debug, or fix BidMachine ads
  on iOS, including: where to begin a fresh integration, adding the pod or SPM package,
  link/build errors after install, Info.plist (ATS, SKAdNetwork, ATT/IDFA), initializing
  the SDK, showing banner, MREC, interstitial, or rewarded ads, delegate/load/show/reward/
  revenue callbacks, error codes, COPPA/GDPR/CCPA consent for kids or EU/California users,
  or feeding BidMachine into AdMob, MAX, or LevelPlay mediation/bidding. Treat even vague,
  partial, or "stuck on setup" iOS requests as in scope. Do NOT trigger for Android, Unity,
  or Flutter work, or purely server-side bidding or dashboard reporting.
license: Apache-2.0
metadata:
  sdk: BidMachine Plus
  platform: ios
  status: released
  source: https://mediation-docs.bidmachine.io/
---

# BidMachine Plus — iOS Integration

Integrate the BidMachine Plus iOS SDK: **install → configure Info.plist → initialize → load ads**.
Swift and Objective-C. **CocoaPods is the primary, most-used integration path; Swift Package
Manager is fully supported as an alternative.**

## Coordinates & version

The pod/package names are `BidMachinePlus` (CocoaPods), `BidMachinePlus-SPM` (SPM), module
`import BidMachinePlus`. The current version is **`0.1.0`**. Full distribution coordinates (sources,
package URLs) are in [`references/distribution.md`](references/distribution.md); don't ask the user
for them.

## Checklist

You MUST create a task for each of these items and complete them in order — the how-to for each is
in the section below. Items 1–2 come first; items 3–8 follow the answers from item 2 (don't add what
wasn't asked for):

1. **Explore project context & requirements** — files, package manager, Info.plist, existing ad/monetization setup, recent commits, and any documented requirements or goals.
2. **Ask clarifying questions** — one at a time; purpose / constraints / success criteria.
3. **Install** — add the dependency via CocoaPods (preferred) or SPM.
4. **Info.plist** — App Transport Security, SKAdNetwork, and ATT (if collecting IDFA).
5. **Initialize** — once at startup, with the chosen demand mode.
6. **Wire ad units** — the requested formats.
7. **Privacy** — regulations for the app's audience.
8. **Verify** — checker + build.

## Requirements

iOS 13.0+, Xcode 16.4+ — treat these as last-known minimums and confirm the current ones against
the docs.

## 1. Explore the project

Before editing, inspect the project and ground the integration in what's already there:

- **Package manager** — a `Podfile` / `*.xcworkspace` / `Pods/` (CocoaPods), or a `Package.swift` /
  `Package.resolved` / `XCRemoteSwiftPackageReference` entries in `*.xcodeproj/project.pbxproj` (SPM).
- The `*.xcodeproj` / `*.xcworkspace`, the `Info.plist`, and the `AppDelegate` / `SceneDelegate` or
  `@main` `App`.
- Any existing ad/monetization setup (preserve it — add BidMachine alongside), recent commits, and
  any documented requirements or goals.
- **Language, UI framework, and concurrency style** — match the project's existing conventions:
  - **Language** — Swift or Objective-C.
  - **UI framework** — SwiftUI, UIKit, or mixed. Determines how a full-screen ad is presented
    (an existing `UIViewController` vs. a top-most-VC lookup from a SwiftUI view) and where the SDK
    instance lives (an `@main App` / `ObservableObject` vs. an `AppDelegate`).
  - **Concurrency** — Swift `async/await` / actors, Combine, GCD (`DispatchQueue.main.async`), or
    completion handlers. Match the project's style; do not introduce a new one.
  **If any of these is unclear or the project mixes styles, ask in step 2.**

## 2. Ask clarifying questions

Ask the essentials — app key (with the package-manager choice when ambiguous), ad formats, demand
mode, privacy audience. You don't have to stall on the answers: scaffold what you can and collect the
missing per-app values in a short "what's left to fill" list.

- **App key** (required to run) — a per-app value from the BidMachine dashboard. Ask for it (with the
  package-manager choice). If it isn't provided yet, **scaffold the integration with a clearly-marked
  `YOUR_APP_KEY` `TODO` and report it as the remaining blocker — don't stall the whole setup.** The
  verifier FAILs on `YOUR_APP_KEY` / `YOUR_PLACEMENT_ID` until replaced with real values. Placement IDs
  are the same — real value if given, else a `TODO`.
  The pod/SPM **source and version** are not asked — they come from
  [`references/distribution.md`](references/distribution.md).
- **Ad formats** wanted (banner / interstitial / rewarded).
- **Demand mode** — AdNetwork (header bidding; the default) or Mediation.
- **Privacy audience** — child-directed? EU/California users?
- **UI framework / concurrency** — only if step 1 left it ambiguous (or the project mixes styles):
  confirm SwiftUI vs UIKit and the concurrency approach (`async/await` vs GCD / completion handlers)
  so the generated ad code matches the project's conventions.
- **Package manager** — ask when the project has **neither** manager (and recommend CocoaPods) or has **both** (let the user pick). With exactly one already present, use it without asking (see §3).

## 3. Install — CocoaPods (preferred) or SPM

**CocoaPods is the primary, most-used path for this SDK; SPM is fully supported as an alternative.**
Pick the path that matches the project:

- **Only one present** → use it; **never switch** the project's package manager (existing `Podfile` ⇒
  CocoaPods; existing package refs ⇒ SPM).
- **Both present** → **ask the user** which path they want; don't pick for them, and don't switch
  whatever already manages the app's other dependencies.
- **Neither present** → **ask the user, recommending CocoaPods** as the preferred BidMachine Plus
  path. Don't silently choose either — and **never silently pick SPM for a greenfield project**.
  (CocoaPods is what most publishers run; SPM is Apple-native with no `pod install`/workspace and
  remains fully supported if the user prefers it.)

> **Step 0 — coordinates + version.** The CocoaPods `source`, the SPM URL, and the version are defined
> in [`references/distribution.md`](references/distribution.md) — read the values from there and
> substitute them into the Podfile / SPM setup. Don't ask the user for them, and don't invent them.

### 3a. CocoaPods path

```ruby title="Podfile"
platform :ios, '13.0'
source 'https://cdn.cocoapods.org/'
source 'https://github.com/bidmachine/CocoaPods-Specs-External'   # BidMachine Plus specs source
use_frameworks!

target 'YourApp' do
    pod 'BidMachinePlus', '0.1.0'
    # Default subspec is Static; /Dynamic also available: pod 'BidMachinePlus/Dynamic'
end
```

Then run `pod install` and open the generated `*.xcworkspace` (not the `*.xcodeproj`).

> The default `BidMachinePlus` pod resolves to the **Static** subspec, which injects the `-ObjC`
> linker flag automatically — on the CocoaPods path you do **not** add `-ObjC` to `OTHER_LDFLAGS`
> manually (that step is only for SPM, §3b).

### 3b. Swift Package Manager path

1. **File → Add Package Dependencies…**
2. URL: `https://github.com/bidmachine/BidMachinePlus-SPM` — the Plus Swift package (`BidMachinePlus-SPM`; coordinates in [`references/distribution.md`](references/distribution.md)).
3. Use the version tag `0.1.0`.
4. Add `-ObjC` to **Build Settings → Other Linker Flags** (`OTHER_LDFLAGS`) — required for the SDK's
   Objective-C category symbols; missing it shows up as `Undefined symbols … _OBJC_CLASS_$_…` at link time.

## 4. Info.plist (common to both install paths)

```xml title="Info.plist"
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

### ATT / IDFA

If you collect the IDFA, add a usage string and request App Tracking Transparency **before the first
ad request**:

```xml
<key>NSUserTrackingUsageDescription</key>
<string>$(APP_NAME) needs your advertising identifier to deliver personalized ads.</string>
```

```swift
import AppTrackingTransparency

ATTrackingManager.requestTrackingAuthorization { _ in /* init / load after this resolves */ }
```

Without ATT consent the SDK runs **non-personalized** — this is distinct from the privacy/regulations
API (ATT governs IDFA access; regulations govern COPPA/age suppression). Details →
[`references/privacy.md`](references/privacy.md).

### SKAdNetwork

Insert the `SKAdNetworkItems` array into `Info.plist` (required for install attribution on iOS 14+).
On the CocoaPods path the full list ships with the SDK — copy it from there. The **SPM package ships no
plist to copy from**, so on the SPM path add a single placeholder entry and a `TODO` to paste the full
list before release. Don't ask the user to provide the IDs.

## 5. Initialize once at startup

`BidMachine.instance(appKey:)` returns the SDK instance — **keep a reference** (you pass it to every
ad unit constructor). Call `initialize` once, typically in `application(_:didFinishLaunching…)` or the
`@main` `App` init.

```swift
import BidMachinePlus

let sdk = BidMachine.instance(appKey: "YOUR_APP_KEY")

let config = InitializationConfigBuilder(integrationType: .adNetwork)  // or .mediation
    .with(loggingEnabled: true)    // remove before release
    .with(testModeEnabled: true)   // remove before release
    .build()

sdk.initialize(config: config) { status, error in
    if let error { print("init failed: \(error.message)") }
}
```

**`integrationType` picks the demand path** (same ad-unit classes either way):

- **`.adNetwork`** — BidMachine is a demand source in an *external* auction: standalone header
  bidding, or feeding a third-party mediation (AdMob / MAX / LevelPlay).
- **`.mediation`** — BidMachine *runs* the auction itself across your demand.

> **`with(mediator:)` is optional and analytics-only.** Add `.with(mediator: MediatorName.admob)`
> (or `.max`, `.levelPlay` — the predefined constants resolve to `"admob"` / `"max"` / `"level_play"`
> — or a custom `String`) *only* in `.adNetwork` mode when integrating through an
> external mediation SDK, so BidMachine can report which mediator it runs under. Omit it everywhere
> else — it does nothing, and an integration never depends on it. In `.mediation` mode there is no
> mediator to declare.

**Before release:** strip `.with(loggingEnabled: true)` and `.with(testModeEnabled: true)`.

## 6. Load ads

Create the ad unit with the `sdk` instance + a placement ID, set its `delegate`, `load()`, then
`show(from:)` once it's loaded (check `isLoaded` / `canShow`). Reload full-screen ads from `didDismiss`
to keep one ready. Release an ad unit by dropping its reference and letting ARC/`deinit` clean it up.
All delegate callbacks fire on the **main thread** — safe to touch UI
directly. Each callback delivers an `AdInfo` (placement, price, precision). Full lifecycle, delegates,
and publisher extras → [`references/ad-units.md`](references/ad-units.md).

## Revenue tracking

`didPayRevenue` fires on a billable impression — forward `adInfo.price` / `adInfo.precision` /
`adInfo.info["networkName"]` to your analytics. Details → [`references/revenue.md`](references/revenue.md).

## 7. Privacy

GDPR (IAB TCF v2), CCPA (US Privacy), and GPP signals are read **automatically** from the CMP
(`UserDefaults`) — no SDK calls. For child-directed apps call `sdk.regulations.setCoppa(true)`; to
suppress user IDs without the COPPA flag use `sdk.regulations.setNonPersonalized(true)`. Do **not**
invent a manual consent boolean — there is none. Details → [`references/privacy.md`](references/privacy.md).

## Win/loss when inside a mediation waterfall

Ad units expose `notifyWin()` / `notifyLoss(winnerEcpm:networkName:)` to report a waterfall round:

```swift
ad.notifyWin()                                          // BidMachine won — call before show(from:)
ad.notifyLoss(winnerEcpm: 2.50, networkName: "admob")   // another network won
```

## 8. Verify the integration

Run the bundled read-only checker:

```bash
python3 scripts/verify_integration.py /path/to/ios/project
```

It scans the Podfile / SPM config, `Info.plist`, and Swift/Obj-C sources for the dependency, the
`-ObjC` flag, init call + mode, ATS/SKAdNetwork/ATT keys, and leftover test-mode / placeholder keys,
printing PASS/WARN/FAIL per check. Then run a build to confirm it compiles, on the simulator (no
signing):

- **CocoaPods:** `xcodebuild -workspace YourApp.xcworkspace -scheme YourApp -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' build CODE_SIGNING_ALLOWED=NO`
- **SPM:** `xcodebuild -project YourApp.xcodeproj -scheme YourApp -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' -resolvePackageDependencies` then the same `build` line with `-project`.

Success is `** BUILD SUCCEEDED **`.

## Troubleshooting — common mistakes

| Symptom | Cause / fix |
|---------|-------------|
| CocoaPods: `Unable to find a specification for 'BidMachinePlus'` | Confirm the `BidMachinePlus` pod name + its spec source (Step 0); run `pod repo update` then `pod install`. |
| SPM: `Undefined symbols … _OBJC_CLASS_$_…` at link time | Add `-ObjC` to **Other Linker Flags** (`OTHER_LDFLAGS`). |
| `Unresolved identifier 'BidMachine'` / missing types | Ensure you integrated the **BidMachine Plus** SDK (`BidMachinePlus` pod / `BidMachinePlus-SPM` package, `import BidMachinePlus`), not the classic `BidMachine` SDK. |
| Opening `.xcodeproj` after `pod install`, build can't find pods | With CocoaPods, open the generated `*.xcworkspace`, not the `*.xcodeproj`. |
| `with(mediator:)` "does nothing" | Correct — it is analytics-only, meaningful only in `.adNetwork` mode with an external mediation SDK (AdMob/MAX/LevelPlay). |
| Ads never fill (`103` no-fill) | Expected intermittently; verify app key, placement ID, and test mode. If attribution is broken, confirm `SKAdNetworkItems` and ATT. |
| Connection / timeout errors (`100` / `102`) | Connectivity; confirm `NSAppTransportSecurity` / `NSAllowsArbitraryLoads`. |
| Test ads / verbose logs in production | Strip `.with(loggingEnabled: true)` and `.with(testModeEnabled: true)` before release. |

## Stuck on an error?

If a build fails or an API won't resolve and the fix isn't obvious, the read-only
**`bidmachine-ios-guide`** agent (when available) diagnoses integration problems against the project's
local API references (`raw/public-api/ios/*` and these `references/*`), using public docs only as a
fallback for release info — consult it, then apply the fix it points to. It is a fallback for
*broken* integrations; fresh integrations are driven by this skill.

## Deeper topics (load on demand)

| Topic | Reference |
|-------|-----------|
| Distribution coordinates — pod/package names, sources, version, install policy | [`references/distribution.md`](references/distribution.md) |
| Ad units — interstitial / rewarded / banner (manual + positioned), AdInfo, delegates, publisher extras | [`references/ad-units.md`](references/ad-units.md) |
| Privacy & regulations — CMP auto-read, `setCoppa`, `setNonPersonalized`, ATT | [`references/privacy.md`](references/privacy.md) |
| Revenue tracking — `didPayRevenue`, precision levels | [`references/revenue.md`](references/revenue.md) |
| Error codes — `BidMachineError` / `BMError`, switching on the numeric `error.code` | [`references/error-codes.md`](references/error-codes.md) |

## Integration checklist

- [ ] Package manager resolved per policy: one present → use it; both → asked the user; neither → asked + recommended CocoaPods; existing manager never switched
- [ ] Dependency added: `pod 'BidMachinePlus'` (CocoaPods) **or** the `BidMachinePlus-SPM` package (SPM) — source/version from `references/distribution.md`
- [ ] CocoaPods: `pod install` run, `*.xcworkspace` opened — **or** SPM: `-ObjC` in `OTHER_LDFLAGS`
- [ ] `NSAppTransportSecurity` / `NSAllowsArbitraryLoads` set
- [ ] `SKAdNetworkItems` array inserted (from the SDK; placeholder + `TODO` if unavailable)
- [ ] `NSUserTrackingUsageDescription` + ATT request if collecting IDFA
- [ ] `BidMachine.instance(appKey:).initialize(config:)` called once at startup; the SDK instance held
- [ ] Correct `integrationType` (`.adNetwork` for header bidding; `with(mediator:)` only when plugged into a 3rd-party mediation, analytics only)
- [ ] `.with(loggingEnabled:)` / `.with(testModeEnabled:)` removed for release builds
- [ ] Full-screen ads reloaded in `didDismiss`; ad units released by dropping the reference (ARC/`deinit`)
- [ ] Privacy: `setCoppa` for child-directed apps; GDPR/CCPA left to the CMP auto-read
- [ ] `{{...}}` coordinates substituted from `references/distribution.md` — no leftover tokens in the project
