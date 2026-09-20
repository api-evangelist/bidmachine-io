# First Look controller — reference mechanics

This file illustrates the **fixed mechanics** of a First Look controller: the cycle, the timeout
guard, the fall-through, the reload, and the cooldown. It is an illustration, not a template.

- **Adapt it, do not copy it verbatim.** The class, field, and method names here are placeholders;
  use the project's conventions.
- It is **mediation-agnostic**: the controller talks to the existing mediation only through the
  abstract `IFallbackAdSource` adapter. There is **no specific mediation** (no MAX/AdMob/LevelPlay) and
  **no app wiring** (no manager, no init order) in this file. Those are project-shaped — see
  [`first-look.md`](first-look.md) for the behavior, the embedding procedure, the BidMachine API
  names, and the per-mediation mapping.
- Build only what the project uses: if there is no rewarded format, skip the rewarded parts; if the
  mediation does not expose a signal, leave it out of the adapter.
- If the host needs to react to close or reward (resume gameplay, clear a "showing" flag, grant a
  reward), expose an event for it and raise it on **both** the BidMachine and the fallback paths —
  wiring it to only one leaves the other path stuck or unrewarded.

The timeout uses `await Task.Delay`, which resumes on the Unity main thread when the controller is
created on the main thread (Unity installs a main-thread synchronization context). The `_cycleId`
guard discards a timeout whose cycle has already moved on.

## The adapter the controller depends on

```csharp
using System;

// Only the members the controller below calls. Shape it to the project's mediation; rename freely.
public interface IFallbackAdSource
{
    void Load();
    void Show(string placement);

    event Action AdLoaded;
    event Action AdLoadFailed;
    event Action AdClosed;     // dismissed or display-failed — the cycle restarts
}

public interface IRewardedFallbackAdSource : IFallbackAdSource
{
    event Action UserRewarded; // the user earned the reward on the mediation side
}
```

## Interstitial controller

```csharp
using System;
using System.Threading.Tasks;
using UnityEngine;
using BidMachineInc.Plus.Api;

public class FirstLookInterstitialController
{
    private readonly BidMachine _sdk;
    private readonly string _placementId;
    private readonly IFallbackAdSource _fallback;
    private readonly int _timeoutMs;

    private InterstitialAd _bmpAd;
    private bool _ready;        // an ad is loaded and ready to show
    private bool _fellThrough;  // this cycle handed off to the mediation
    private int _cycleId;       // invalidates stale timeout callbacks
    private int _retry;

    public bool IsReady => _ready;

    public FirstLookInterstitialController(BidMachine sdk, string placementId, IFallbackAdSource fallback, int timeoutMs)
    {
        _sdk = sdk;
        _placementId = placementId;
        _fallback = fallback;
        _timeoutMs = timeoutMs;

        _fallback.AdLoaded     += OnFallbackLoaded;
        _fallback.AdLoadFailed += OnFallbackFailed;
        _fallback.AdClosed     += OnFallbackClosed;

        BeginCycle();
    }

    public void Show(string placement)
    {
        if (!_ready) return;
        _ready = false;
        if (_fellThrough) _fallback.Show(placement);
        else _bmpAd.Show();
    }

    private void BeginCycle()
    {
        _cycleId++;
        _ready = false;
        _fellThrough = false;
        InstantiateBmp();
        _bmpAd.Load();
        if (_timeoutMs > 0) ScheduleTimeout(_cycleId, _timeoutMs);
    }

    private async void ScheduleTimeout(int cycleId, int delayMs)
    {
        try { await Task.Delay(delayMs); }
        catch { return; }

        // Skip if the cycle moved on, BidMachine already answered, or we already fell through.
        if (cycleId != _cycleId || _ready || _fellThrough) return;

        Debug.Log("[FirstLook] interstitial: BidMachine timed out, falling through");
        FallThrough();
    }

    // ── BidMachine side ──────────────────────────────────────────────
    private void InstantiateBmp()
    {
        DisposeBmp();
        _bmpAd = new InterstitialAd(_sdk, _placementId);
        _bmpAd.Loaded     += OnBmpLoaded;
        _bmpAd.LoadFailed += OnBmpLoadFailed;
        _bmpAd.ShowFailed += OnBmpShowFailed;
        _bmpAd.Closed     += OnBmpClosed;
    }

    private void OnBmpLoaded(object sender, AdLoadedEventArgs args)
    {
        if (_fellThrough) return; // the timeout already handed off
        _ready = true;
        _retry = 0;
    }

    private void OnBmpLoadFailed(object sender, AdLoadFailedEventArgs args)
    {
        if (_fellThrough) return;
        FallThrough(); // no-fill — hand off to the mediation
    }

    private void OnBmpShowFailed(object sender, AdShowFailedEventArgs args) => BeginCycle();
    private void OnBmpClosed(object sender, AdClosedEventArgs args)         => BeginCycle();

    private void FallThrough()
    {
        _fellThrough = true;
        InstantiateBmp(); // detach and abandon the in-flight BidMachine request
        _fallback.Load();
    }

    private void DisposeBmp()
    {
        if (_bmpAd == null) return;
        _bmpAd.Loaded     -= OnBmpLoaded;
        _bmpAd.LoadFailed -= OnBmpLoadFailed;
        _bmpAd.ShowFailed -= OnBmpShowFailed;
        _bmpAd.Closed     -= OnBmpClosed;
        _bmpAd.Dispose();
        _bmpAd = null;
    }

    // ── Mediation side (fall-through) ────────────────────────────────
    private void OnFallbackLoaded()
    {
        if (!_fellThrough) return;
        _ready = true;
        _retry = 0;
    }

    private void OnFallbackFailed()
    {
        if (!_fellThrough) return;
        EnterCooldown(); // both BidMachine and the mediation failed this cycle
    }

    private void OnFallbackClosed() => BeginCycle();

    private async void EnterCooldown()
    {
        _retry++;
        int delaySec = (int)Math.Pow(2, Math.Min(6, _retry));
        try { await Task.Delay(delaySec * 1000); }
        catch { return; }
        BeginCycle();
    }
}
```

## Rewarded: the delta

The rewarded controller is the same shape, with three differences:

- The BidMachine ad is a `RewardedAd`, and `InstantiateBmp` also subscribes to
  `UserQualifiedForReward` (and `DisposeBmp` unsubscribes it).
- The fallback is an `IRewardedFallbackAdSource`, and the controller subscribes to its `UserRewarded`.
- The controller exposes `public event Action Rewarded;` and raises it from **either** side, so the
  caller grants the reward in one place.

```csharp
// In InstantiateBmp(), also subscribe:
_bmpAd.UserQualifiedForReward += (s, e) => Rewarded?.Invoke();

// In the constructor, also subscribe:
((IRewardedFallbackAdSource)_fallback).UserRewarded += () => Rewarded?.Invoke();
```
