# Privacy & Regulations — iOS

## Auto-read — no code required

The SDK reads IAB-standard signals from `UserDefaults` before every ad request. With a
certified CMP, **no privacy API calls are needed** for GDPR/CCPA.

| Standard       | Keys                                    | Coverage                      |
|----------------|-----------------------------------------|-------------------------------|
| IAB TCF v2     | `IABTCF_TCString`, `IABTCF_gdprApplies` | GDPR (EU/EEA/UK)              |
| IAB US Privacy | `IABUSPrivacy_String`                   | CCPA (California)             |
| IAB GPP        | `IABGPP_HDR_GppString`, `IABGPP_GppSID` | All US states, Brazil, Canada |

## Manual API — two signals with no IAB key

### `setCoppa` — child-directed (COPPA)

Marks the app child-directed; also enables non-personalized mode internally.

```swift
sdk.regulations.setCoppa(true)   // setter only — there is no isCoppa getter
```

### `setNonPersonalized` — suppress IDs without COPPA

Suppresses GAID/IDFA, geo, user-agent, etc. **without** the COPPA flag.

```swift
sdk.regulations.setNonPersonalized(true)   // setter only — there is no isNonPersonalized getter
```

## Which one

| Scenario                                       | Method                     |
|------------------------------------------------|----------------------------|
| Children's app (under 13, US)                  | `setCoppa(true)`           |
| User under 18 (UK AADC, Brazil Digital ECA)    | `setNonPersonalized(true)` |
| User under 16 (US state laws — TX, UT, LA)     | `setNonPersonalized(true)` |
| Publisher wants to suppress IDs for any reason | `setNonPersonalized(true)` |
| GDPR consent                                   | No code — CMP auto-read (IAB TCF v2)         |
| CCPA opt-out                                   | No code — CMP auto-read (IAB US Privacy/GPP) |

> `setCoppa(true)` enables `setNonPersonalized(true)` internally — don't call both.

## ATT (iOS-specific)

IDFA access requires App Tracking Transparency. Add `NSUserTrackingUsageDescription` to
Info.plist and request authorization (`ATTrackingManager.requestTrackingAuthorization`)
before the first ad request — use the form that matches the project: the completion-handler
`requestTrackingAuthorization { status in … }`, or in an `async/await` codebase
`await ATTrackingManager.requestTrackingAuthorization()`. Without consent, the SDK runs non-personalized — this is
distinct from the regulations API above (ATT governs IDFA access; regulations govern
COPPA/age suppression). The SDK does not track the user's age.
