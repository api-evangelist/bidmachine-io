# iOS Distribution Coordinates

The BidMachine Plus iOS coordinates. Current version: **`0.1.0`**.

## 1. Coordinates

### CocoaPods — recommended / default

| Field | Value |
|-------|-------|
| Pod name | `BidMachinePlus` (optional static subspec `BidMachinePlus/Static`) |
| Specs source | `https://github.com/bidmachine/CocoaPods-Specs-External` |
| Version | `0.1.0` |

The public CDN source (`https://cdn.cocoapods.org/`) is the primary source; the specs source above
is the fallback.

### Swift Package Manager — supported alternative

| Field | Value |
|-------|-------|
| Package name | `BidMachinePlus-SPM` (product/module `BidMachinePlus`, `import BidMachinePlus`) |
| Package URL | `https://github.com/bidmachine/BidMachinePlus-SPM` |
| SPM ref | tag `0.1.0` |

## 2. Install-path policy

- **CocoaPods is recommended / default; SPM is a supported alternative.**
- Existing CocoaPods (a `Podfile` / `*.xcworkspace`) → **use CocoaPods**.
- Existing SPM only (package refs, no `Podfile`) → **use SPM**.
- Both present → **ask the user** which path to use.
- Neither present → **ask the user, recommending CocoaPods**.
- **Never** silently choose a manager, and **never** switch the project's existing package manager.
