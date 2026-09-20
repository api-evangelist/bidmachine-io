# First Look — behavior and how to embed it

First Look requests a BidMachine Plus ad before the existing mediation, against a timeout. If
BidMachine fills in time, that ad is shown; on a no-fill or timeout, the request falls through to the
project's existing mediation, which runs as before. No prices or signals pass between the two, and the
only value you tune is the timeout.

This page describes two things. The **behavior** First Look must reproduce is fixed — match it. **How
that behavior is fitted into a project** is free — the structure and the names follow the project's
architecture and conventions. The reference design has a manager, one controller per ad format, an
adapter over the existing mediation, and interfaces between them. Reproduce its logic; size and name
the pieces to the project at hand.

## The behavior to reproduce

First Look runs one independent cycle per ad format. A cycle moves through these states:

- **Request BidMachine first.** At the start of a cycle, create a BidMachine ad for the format's
  placement, start its load, and arm a timeout. The cycle is now waiting.
- **BidMachine wins.** If BidMachine loads before the timeout, the cycle is ready and the ad to show
  is the BidMachine one.
- **Fall through.** If BidMachine returns a no-fill (load failed), or the timeout fires before
  BidMachine answers, the cycle hands off: it abandons the in-flight BidMachine request and asks the
  existing mediation to load. When the mediation loads, the cycle is ready and the ad to show is the
  mediation's.
- **Guard against a stale timeout.** A timeout belongs to the cycle that armed it. If it fires after
  that cycle already resolved — BidMachine had loaded, the cycle had already fallen through, or a
  newer cycle has started — it does nothing. Track the current cycle (an id or token) and its state so
  a late timer cannot trigger a second fall-through or disturb a fresh cycle.
- **Show.** When the game asks to show the format, show whichever side is ready (BidMachine if it won,
  the mediation if the cycle fell through), then mark the cycle not-ready. If nothing is ready, show
  nothing.
- **Reload on close.** After the shown ad closes, or if showing fails, start a fresh cycle from the
  top, so an ad is preparing for the next request.
- **Back off when both fail.** If BidMachine and the mediation both fail to load in the same cycle,
  wait a short delay that grows on repeated failures up to a cap, then start a new cycle. This avoids
  hammering both on a dead network.
- **Grant the reward from either side.** For rewarded, grant the reward when the user qualifies, from
  whichever side showed the ad: BidMachine's reward signal or the mediation's reward callback. Route
  both to the same grant path.

The decision to participate lives on BidMachine's server; the client does no price comparison and has
no thresholds. Honor the answer: show on a BidMachine load, fall through on a no-fill or timeout, and
otherwise let the mediation run as it does today. However the timeout is implemented, its callback must
run on the Unity main thread and must respect the stale-timeout guard above.

## Initialization order

Initialize once at startup, in this order:

1. **BidMachine first.** Get the SDK instance and build a config in `IntegrationMode.Mediation`, with
   `WithLoggingEnabled` and `WithTestModeEnabled` gated on `Debug.isDebugBuild` so they are on in the
   Editor and Development Builds and off in release. Subscribe to the initialized event, then start
   initialization.
2. **The existing mediation next.** When BidMachine reports ready, run the project's existing mediation
   initialization, and wait for the mediation's own ready signal.
3. **Start the controllers** once the mediation is ready.

Relocate, do not duplicate: move the project's current mediation-init call into step 2, and replace
its old call site (usually app startup) with a call to the First Look manager's init. The mediation is
then initialized exactly once, after BidMachine.

## How to embed it in a project

The aim is to add First Look in front of the working mediation while changing the existing ad code as
little as possible.

1. **See how the project reaches its mediation.** Two shapes are common, and they call for different
   amounts of work:
   - The mediation already sits behind the project's own layer — a manager, service, or wrapper that
     the game calls. Wrap that layer; do not add a second one on top of it.
   - The mediation SDK is called directly inline, from event handlers such as a timer tick, a button
     press, or a level-complete callback. Here, first pull those calls into one thin layer so there is
     a single place that loads and shows each format. The call sites then ask that layer to show
     instead of calling the SDK. Introduce a new abstraction only in this case.

2. **Preserve the mediation's behavior.** The existing loads, shows, and callbacks keep working as
   they did; First Look reaches them on the fall-through path through an adapter. Lift code behind an
   interface rather than rewriting it. The waterfall, mediation groups, and ad-unit settings stay as
   they are.

3. **Build the pieces, sized to the project.** Mirror the reference design conceptually:
   - A **manager** that owns the initialization order and exposes a show entry point per format.
   - One **First Look controller** per ad format the project actually uses. A game with only
     interstitials has no rewarded controller.
   - An **adapter** over the existing mediation that exposes only the operations a controller calls,
     for only the formats in use. An event or method the controller does not use does not enter the
     interface.
   - **Interfaces** only where they earn their place. With a single mediation and one format, a full
     interface may be unnecessary; with several, it keeps the controller independent of the mediation.

4. **Keep names and shape native to the project.** Class, interface, and method names follow the
   project's conventions — there are no required names. If a manager-like class already exists, extend
   it instead of adding a competing one. Match the project's namespaces, formatting, and
   `MonoBehaviour` patterns. Keep the per-app values (BidMachine app key and placements, the mediation
   ad-unit IDs, the timeout) in one place, split by platform if the iOS and Android values differ.

5. **Route both the show and the result through the controller.** Where the game used to trigger an
   ad, it now asks the First Look manager to show that format, and the manager chooses between
   BidMachine and the mediation internally — the gameplay code that decides *when* to show does not
   change. The same goes for the result: whatever the game does on close or reward (resume gameplay,
   clear a "showing" flag, grant the reward) must be driven by the controller on **both** paths,
   BidMachine and the fallback — not wired to BidMachine only. The controller is the single owner of
   the format's lifecycle, so remove the mediation's own close-and-reload or reward/close handlers
   that touched that state; left in place, they run in parallel and the two paths behave differently.

6. **Offer a choice when the architecture allows several shapes.** If more than one integration is
   reasonable — for example, extending an existing manager versus adding a dedicated First Look layer
   beside it — present the options with their trade-offs at the plan step and let the user pick before
   you write code.

## Sequential loading: the fallback loads on demand

First Look is sequential, not parallel. The fallback mediation must load **only when the controller
falls through** to it — never ahead of time, alongside BidMachine. So the adapter's `Load()` has to
start a real load of the mediation and report back through its loaded / failed events; it must not
assume an ad is already waiting.

This breaks when the mediation auto-caches — keeps an ad loaded on its own, or reloads automatically
after each close — because then it is loading alongside BidMachine instead of after a fall-through.
Detect it during the explore step and turn it off. If the project has no explicit ad loading at all —
no manual load/cache calls and no reload-on-close — assume the mediation auto-caches under the hood (a
live app that serves ads is caching somehow; a missing-loading bug is far less likely in a shipping
project), not that there is nothing to change:

- **Auto-reload in the project's own code** (the app re-loads the mediation from a close callback, or
  sets an autocache flag it controls): remove it and let the First Look controller drive the loads.
- **Autocache inside the mediation SDK**: confirm the SDK supports manual loading — check the
  mediation's documentation online *and* find the disable-autocache / manual-load API in the SDK
  installed in the project — then turn autocache off and load on demand from the adapter.
- **No manual-load option exists**: stop and raise it with the user as a blocker, asking how to
  disable autocache for their mediation. Without on-demand loading there is no true First Look.

## BidMachine Plus API (fixed names)

These names are the plugin's real API; call them exactly. Confirm against the installed plugin's
`Runtime/Api/*.cs` if anything looks off. All types live in `BidMachineInc.Plus.Api`.

- **SDK:** `BidMachine.GetInstance(appKey)` returns the instance. `Initialized` (an
  `EventHandler<SdkInitializedEventArgs>`, with `args.Error` non-null on failure) signals readiness;
  `Initialize(config)` starts it. `Regulations.SetCoppa(bool)` / `SetNonPersonalized(bool)` cover
  privacy.
- **Config:** `new InitializationConfigBuilder(IntegrationMode.Mediation)`, with
  `WithLoggingEnabled(bool)`, `WithTestModeEnabled(bool)`, `WithMediator(string)` (analytics only),
  and `Build()`.
- **Ads:** `new InterstitialAd(sdk, placementId)` and `new RewardedAd(sdk, placementId)`. Methods
  `Load(...)`, `Show()`, `Dispose()`. Events `Loaded`, `LoadFailed`, `Shown`, `ShowFailed`, `Closed`,
  plus `UserQualifiedForReward` on rewarded. `Loaded` carries an `AdInfo` with `Price` and
  `RawData["networkName"]` for reporting.

Subscribe to a BidMachine ad's events before loading it, and `Dispose()` it when a cycle ends or hands
off, so a stale instance does not deliver events into a new cycle. Events arrive on the Unity main
thread.

## Mapping the adapter to the project's mediation

The adapter's surface is shaped from both ends: what the controller needs, and how the project's
mediation expresses it. The controller needs, at most, a way to load, a way to show, and the loaded /
failed / closed signals (plus a reward signal for rewarded). Include only what the controller uses and
only the formats in use; derive any signal the mediation does not provide directly.

This table maps those operations to three common mediations. Names differ by SDK version, so confirm
against the version the project has installed, and prefer the project's existing usage as the
reference. Where the game already wraps its mediation in its own manager, point the adapter at that
wrapper instead of the SDK.

| Operation                | AppLovin MAX                                   | Google AdMob                                        | Unity LevelPlay                    |
|--------------------------|------------------------------------------------|-----------------------------------------------------|------------------------------------|
| Load                     | `MaxSdk.LoadInterstitial` / `LoadRewardedAd`   | load on an `InterstitialAd` / `RewardedAd` instance | `LevelPlay…Ad.LoadAd()`            |
| Show                     | `MaxSdk.ShowInterstitial` / `ShowRewardedAd`   | `.Show()` on the loaded instance                    | `.ShowAd()` on the loaded instance |
| Loaded signal            | `OnAdLoadedEvent`                              | `OnAdLoaded`                                        | `OnAdLoaded`                       |
| Failed signal            | `OnAdLoadFailedEvent`                          | `OnAdFailedToLoad`                                  | `OnAdLoadFailed`                   |
| Closed signal            | `OnAdHiddenEvent` (+ `OnAdDisplayFailedEvent`) | `OnAdFullScreenContentClosed` (+ failed-to-show)    | `OnAdClosed` (+ display-failed)    |
| Reward signal (rewarded) | `OnAdReceivedRewardEvent`                      | `OnUserEarnedReward`                                | `OnAdRewarded`                     |
