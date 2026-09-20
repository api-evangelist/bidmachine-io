---
name: bidmachine-unity
description: >
  Add BidMachine Plus as a First Look layer in front of a Unity game's existing ad mediation
  (C#, package com.bidmachine.plus). Use this whenever someone wants to request an interstitial or
  rewarded ad from BidMachine Plus before their current mediation and fall through to it
  (AppLovin MAX, Google AdMob, Unity LevelPlay, or another) on a no-fill or timeout: installing the
  plugin via Unity Package Manager scoped registries, resolving External Dependency Manager,
  initializing the SDK in Mediation mode, and wiring a First Look controller that requests
  BidMachine first and hands off to the existing waterfall otherwise. Covers setting up the recommended Unity
  MCP server so the agent can install packages and read compile errors. Treat any
  "BidMachine First Look on Unity" request as in scope. Stay out when the work targets Android-native
  or iOS-native (Kotlin/Java/Swift), or is a plain BidMachine install with no fall-through to an
  existing mediation.
license: Apache-2.0
---

# BidMachine Plus — Unity First Look

First Look requests a BidMachine Plus ad before the existing mediation, on a timeout. If BidMachine
fills in time, you show its ad. On a no-fill or timeout, the request falls through to the game's
existing mediation, which runs as it did before. No prices or signals pass between the two.

This skill integrates First Look for **interstitial and rewarded** ads. It does not replace the
project's mediation and does not change banners — it adds a layer in front and preserves what is
already there.

## What you are building

- A **manager** that initializes BidMachine Plus, then the existing mediation, then starts a
  controller per format. If the project already has an ad manager, extend that one; otherwise add one
  with a name that does not collide. (The reference design calls it `AdManager`; the name is yours.)
- One First Look controller per format (interstitial, rewarded). Each requests BidMachine first, arms a
  timeout, falls through to the existing mediation on a no-fill or timeout, and reloads on close.
- A thin adapter that wraps the project's **existing** mediation calls so the controller stays
  mediation-agnostic. Its surface is only what the controller calls (a load, a show, and the loaded /
  failed / closed signals, plus a reward signal for rewarded), not a fixed list. You wrap the working
  code; you do not rewrite it.

The behavior and the embedding procedure are in [`references/first-look.md`](references/first-look.md);
a reference controller to adapt is in [`references/controller-reference.md`](references/controller-reference.md).

## Checklist

Create a task for each item and complete them in order. The how-to for each is in the section below.
Items 1–3 gather context and choices; 4–8 act on them.

1. **Choose the tooling path** — Unity MCP (recommended) or manual.
2. **Explore the project** — mediation in use, where ads are shown, existing privacy calls, package state.
3. **Confirm the mediation and collect IDs** — app key, placements, existing ad-unit IDs, timeout.
4. **Install** — two scoped registries, then the `com.bidmachine.plus` package.
5. **Plan** — present the First Look change and get approval before editing.
6. **Implement** — the manager, the controllers, and the adapter over the existing mediation.
7. **Privacy** — mirror the project's existing COPPA / non-personalized settings onto BidMachine.
8. **Verify** — compile and check the console (MCP), or hand the build steps to the user (manual).

## Requirements

Unity 2021.3+ (the plugin's minimum — the `unity` field in its `package.json`), and the game's existing
ad mediation already integrated and working, since First Look needs something to fall through to. That
mediation can be a UPM package or live under `Assets/` — either works.

## 1. Choose the tooling path

First Look works best when the agent can install the package and read compile errors directly. Before
anything else, ask the user one question with three options and wait for the answer:

- **Unity MCP is already running** — an MCP server is connected to the open project. Confirm it is
  reachable (list packages or read the console). If it is not, report that and offer to help set it up.
- **Set up Unity MCP** — walk the user through installing and starting the recommended server, then
  continue on the MCP path. Steps are in [`references/mcp-setup.md`](references/mcp-setup.md).
- **Manual, no MCP** — you write the C# code; the user drives the Unity Editor. They add the two
  scoped registries and install the package from your exact instructions (step 4), then build and
  report console output back to you. You may instead edit `Packages/manifest.json` yourself if the
  user prefers, but you cannot operate the Editor (close the scoped-registry popup, run the
  resolver, read the console), so you cannot verify the install or fix compile errors in the same
  loop. State this trade-off plainly.

The recommended server is CoplayDev Unity MCP (<https://github.com/CoplayDev/unity-mcp>), which
supports a range of Unity versions and can add scoped registries, install packages, and read the
console. On the MCP path, prefer it for every install and compile step below.

**Tell the user up front:** when the scoped registry is added (step 4), Unity shows a one-time
"Importing a scoped registry" popup that they must click **Close** for the integration to continue —
the agent and MCP cannot dismiss it. See [`references/install.md`](references/install.md).

## 2. Explore the project

Ground the integration in what is already there. Before editing:

- **Mediation in use** — read `Packages/manifest.json` and search the game's own scripts (not the SDK
  folders) for ad calls. Identify which mediation actually runs: AppLovin MAX (`MaxSdk.*`), Google
  AdMob (`GoogleMobileAds.*`), Unity LevelPlay (`IronSource.*` / `LevelPlay.*`), or another.
- **Where ads are shown** — the scripts and methods that load and show interstitial and rewarded ads,
  where the mediation is initialized, and how a reward is granted.
- **Auto-loading** — whether the mediation auto-caches or reloads on close (in the project's code or
  under the hood), since First Look needs it to load on demand. See
  [`references/first-look.md`](references/first-look.md).
- **Privacy calls** — any COPPA / child-directed or non-personalized / consent settings the project
  already applies to its mediation.
- **Package state** — existing `scopedRegistries` and `dependencies`, and whether External Dependency
  Manager is present as a UPM package or imported under `Assets/`.
- **Code style** — namespace, naming, async style, how `MonoBehaviour`s are organized. Match it.

## 3. Confirm the mediation and collect IDs

**Confirm, don't ask blind.** State what you found in step 2 — the mediation in use and the actual
script that shows the ads (for example, "AppLovin MAX, shown from your main game-loop script") — and
ask the user to confirm before you build on it.

Collect the values First Look needs. The existing mediation's ad-unit IDs are usually already in the
project — find them and present for confirmation. The First Look timeout defaults to ~15000 ms (tunable
from reporting). The new values are the **BidMachine app key** and a **placement ID per format**
(interstitial, rewarded), from the BidMachine dashboard.

Ask for those as values the user can paste in a single reply — and that actually capture what they
paste — offering "use placeholders for now" as the alternative in the same ask. For example: *"Paste
your BidMachine app key and interstitial/rewarded placement IDs, or say to use placeholders for now."*
Don't pose it as a pick-one "provide now vs later" prompt: that doesn't capture the values, so the run
continues without them. If the user pastes them, use them; if they choose placeholders (or don't have
them yet), scaffold clearly-marked `YOUR_…` placeholders and report them as the remaining blocker —
the verifier FAILs on leftover placeholders.

## 4. Install

Install `com.bidmachine.plus` from the BidMachine scoped registry, with its External Dependency
Manager dependency resolved through UPM. [`references/install.md`](references/install.md) is the full
recipe — coordinates, the two registries and when each is needed, reconciling with an existing
`manifest.json`, the MCP and manual paths, the scoped-registry popup, the EDM duplicate check, and
resolving the native dependencies.

## 5. Plan, then get approval

Before editing code, research how the existing mediation is structured and write a short plan: which
files you add or change (extend the existing ad manager if there is one, or add a non-conflicting one;
the controllers; the adapter), how the controller will call the project's existing load/show, where
the mediation's init moves to and where the manager's init replaces it, and how the show sites change.
Present it and ask the user to approve or adjust. Do not start editing on assumptions.

## 6. Implement

Follow [`references/first-look.md`](references/first-look.md) for the behavior and the embedding
procedure, and [`references/controller-reference.md`](references/controller-reference.md) for the
controller's fixed mechanics — adapt it to the project, don't copy it verbatim.

## 7. Privacy

Mirror the project's existing privacy settings onto BidMachine at init: for each privacy flag the
project sets on its mediation, make the matching `sdk.Regulations` call with the **same value** the
project passes there. These flags are usually per-user (from an age gate, a consent prompt, or a
stored setting), so pass the same source the project already uses:

- **Child-directed (COPPA):** if the project sets a COPPA / age-restricted flag on its mediation, call
  `sdk.Regulations.SetCoppa(value)` with that same value.
- **Non-personalized ads:** if the project toggles personalized ads, call
  `sdk.Regulations.SetNonPersonalized(value)` with that same value.

GDPR (IAB TCF), CCPA, and GPP need no calls — BidMachine reads them from the CMP automatically, the
same signal the mediation already uses.

## 8. Verify

**MCP path:** install confirmed, then trigger a recompile and read the console. Resolve any errors
your changes caused — fix the trivial ones, and for the rest gather the error and the surrounding code
and decide with the user. Run the bundled checker:

```bash
python3 scripts/verify_integration.py /path/to/unity/project
```

It prints PASS / WARN / FAIL for the registry, the package, External Dependency Manager, the init mode,
a BidMachine ad, and leftover placeholders.

**Manual path:** you cannot read the console, so the build is the user's to run. Have them install per
step 4, close the scoped-registry popup, run the Android/iOS resolver, and report console output
back to you. You can still run `verify_integration.py` on the project files yourself, and diagnose from
what the user reports.

**Stuck on an error?** The read-only **`bidmachine-unity-guide`** agent (when available) diagnoses
registry/UPM, EDM duplicates, export, and First Look controller problems against the installed plugin
source. Consult it, then apply the fix it points to.

## Integration checklist

- [ ] Tooling path chosen (MCP or manual); on MCP, the server is reachable
- [ ] Existing mediation identified and confirmed with the user
- [ ] App key, placements, existing ad-unit IDs, and timeout collected (or `TODO` placeholders noted)
- [ ] Both scoped registries added; `com.bidmachine.plus` installed; External Dependency Manager resolved
- [ ] No duplicate External Dependency Manager under `Assets/`
- [ ] First Look change planned and approved before editing
- [ ] BidMachine initialized once in `IntegrationMode.Mediation`; the existing mediation init moved into the manager after BidMachine (not duplicated)
- [ ] Controllers request BidMachine first, fall through on no-fill/timeout, reload on close
- [ ] Existing mediation preserved behind an adapter, not rewritten
- [ ] Fallback mediation loads on demand (autocache / auto-reload off); the adapter's `Load()` starts a real load
- [ ] Close and reward reach the game on both paths (BidMachine and fallback); the controller is the single owner — the mediation's own parallel close-reload / reward handlers removed
- [ ] `WithLoggingEnabled` / `WithTestModeEnabled` gated on `Debug.isDebugBuild` (off in release); BidMachine ads `Dispose()`-ed
- [ ] Privacy: the project's COPPA / non-personalized settings mirrored onto `sdk.Regulations`; GDPR/CCPA left to the CMP
- [ ] Compiles clean (console checked on MCP, or built by the user on manual)
