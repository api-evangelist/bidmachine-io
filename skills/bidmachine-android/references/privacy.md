# Privacy & Regulations — Android

## Auto-Read (No Code Required)

The SDK automatically reads IAB-standard privacy signals from `SharedPreferences` (Android) and `UserDefaults` (iOS). If your app uses a certified CMP (Consent Management Platform), no privacy-related API calls are needed.

| Standard | Keys | Coverage |
|----------|------|----------|
| IAB TCF v2 | `IABTCF_TCString`, `IABTCF_gdprApplies` | GDPR (EU/EEA/UK) |
| IAB US Privacy | `IABUSPrivacy_String` | CCPA (California) |
| IAB GPP | `IABGPP_HDR_GppString`, `IABGPP_GppSID` | All US states, Brazil, Canada, etc. |

The CMP writes these values; the SDK reads them before every ad request. Publisher-side code is not involved.

## Manual API

Two signals have **no standard IAB storage key** and must be set explicitly by the publisher when applicable.

### `setCoppa`

Marks the app as child-directed for COPPA purposes. Internally also enables non-personalized mode — all sensitive user identifiers are suppressed from bid requests.

```kotlin
sdk.regulations.setCoppa(true)
```

### `setNonPersonalized`

Suppresses all sensitive user identifiers (GAID/IDFA, geo, user-agent, etc.) from bid requests **without** setting the COPPA flag. Use this for age-based content restrictions or any scenario where the publisher wants to omit user IDs.

```kotlin
sdk.regulations.setNonPersonalized(true)
```

### When to Use Which

| Scenario | Method |
|----------|--------|
| Children's app (under 13, US) | `setCoppa(true)` |
| User under 18 (UK AADC, Brazil Digital ECA) | `setNonPersonalized(true)` |
| User under 16 (US state laws — TX, UT, LA) | `setNonPersonalized(true)` |
| Publisher wants to suppress IDs for any reason | `setNonPersonalized(true)` |
| GDPR consent | No code needed — auto-read from CMP (IAB TCF v2) |
| CCPA opt-out | No code needed — auto-read from CMP (IAB US Privacy / GPP) |

> `setCoppa(true)` automatically enables `setNonPersonalized(true)` internally. You do not need to call both.

## Design Rationale

This API is aligned with IAB privacy standards (TCF v2, GPP, US Privacy) and common industry practice:

- **GDPR / CCPA / GPP** are handled via auto-read from CMP storage — the standard IAB approach. No manual boolean (`setDoNotSell`, `setHasUserConsent`) is needed because the CMP already writes standardized strings that carry more information than a simple boolean.
- **COPPA** has no IAB storage key — it is a publisher-level decision (the app is child-directed or not), so it must be set explicitly.
- **Non-personalized mode** covers age-based regulations beyond COPPA (UK AADC, Brazil, US state laws) where user IDs must be suppressed but the COPPA flag does not apply. The SDK does not track the user's age — the publisher determines when to enable this mode.
