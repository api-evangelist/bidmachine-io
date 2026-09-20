# Install — registries, package, native dependencies

The plugin is distributed through a scoped registry and pulls its native SDKs through External
Dependency Manager (EDM4U). Add two registries, install one package, then resolve the native Android
and iOS dependencies.

## Coordinates

| Item                | Value                                                                                                         |
|---------------------|---------------------------------------------------------------------------------------------------------------|
| Package             | `com.bidmachine.plus`                                                                                         |
| Version             | `0.1.0`                                                                                                       |
| BidMachine registry | name `BidMachine Registry`, url `https://npm.bidmachine.com`, scope `com.bidmachine`                          |
| OpenUPM registry    | name `package.openupm.com`, url `https://package.openupm.com`, scope `com.google.external-dependency-manager` |
| EDM4U dependency    | `com.google.external-dependency-manager` (resolved from OpenUPM, or any UPM source the project already uses)  |

## Why two registries

`com.bidmachine.plus` depends on `com.google.external-dependency-manager`. The BidMachine registry
serves only `com.bidmachine.*`, so without a registry that serves EDM4U the package fails to resolve.
OpenUPM serves it. If the project already resolves EDM4U through UPM another way (a package from
another registry, a Git URL, or a tarball), that source is enough and the OpenUPM entry is optional —
check `Packages/manifest.json` first. A copy under `Assets/` does not count, since it is not a UPM
package; install EDM4U via UPM and remove the `Assets/` copy.

## Install paths

Which path applies depends on the tooling choice from step 1 of the skill: the agent installs through
MCP, or the user installs through the Editor UI from the agent's instructions.

Whichever path, **reconcile with what's already in `Packages/manifest.json`**: add a scoped registry
only when no entry with that URL exists (otherwise reuse it), and add a scope to a registry only when
it doesn't already cover the package. UPM matches scopes by prefix, so an existing `com.google` or
`com` already covers `com.google.external-dependency-manager`, and `com` or `com.bidmachine` already
covers `com.bidmachine.plus`. Don't create a duplicate registry or a duplicate scope.

### MCP

Through the Unity MCP server: `list_registries` first, add each registry that isn't already present
(or the missing scope on one that is), then add the package. Have the user close the scoped-registry
popup when it appears (see below), then read the console to confirm a clean compile. The server can
also list installed packages to verify the result.

### Editor UI (the manual path)

Without MCP, the user does this from the agent's exact instructions:

1. **Edit > Project Settings > Package Manager > Scoped Registries** — add each registry from the
   table above that isn't already listed; if one is listed, add only the scope it's missing.
2. **Window > Package Manager**, switch the source to **My Registries**, find **BidMachine Plus**, and
   install it; click **Close** on the scoped-registry popup if it appears.

This is the safer manual default: it keeps the user in control, surfaces any resolution error
directly, and avoids hand-merging JSON.

### Editing `Packages/manifest.json` (alternative)

An alternative to the UI — the agent can apply this directly only if the user prefers it. Add both
registries to `scopedRegistries` and the package to `dependencies`:

```json
{
  "scopedRegistries": [
    {
      "name": "BidMachine Registry",
      "url": "https://npm.bidmachine.com",
      "scopes": ["com.bidmachine"]
    },
    {
      "name": "package.openupm.com",
      "url": "https://package.openupm.com",
      "scopes": ["com.google.external-dependency-manager"]
    }
  ],
  "dependencies": {
    "com.bidmachine.plus": "0.1.0"
  }
}
```

Unity resolves the package and its EDM4U dependency on the next focus. Merge into any existing
`scopedRegistries` / `dependencies`: don't duplicate a registry that's already there by URL, or a
scope a registry already covers (see *Install paths* above).

## Scoped-registry popup

Adding a scoped registry by a `manifest.json` change — which is what both the MCP `add_registry` and a
manual edit do — makes Unity show a one-time **"Importing a scoped registry — A new scoped registry is
now available"** popup. It is informational: the user clicks **Close** to dismiss it (which opens the
Package Manager settings). There is no setting to disable it, and neither the agent nor MCP can close
it — it is a modal Editor dialog. So on the MCP path, tell the user to click Close for the integration
to continue; if an install seems to hang, this popup waiting is the usual reason. (Adding the
registries through the Project Settings UI instead does not raise it.)

## Duplicate External Dependency Manager

EDM4U is sometimes already present, imported by hand under `Assets/ExternalDependencyManager` or
`Assets/PlayServicesResolver`. With the UPM package also installed, two copies of its assemblies load
and the console shows duplicate-assembly or type-conflict errors. Keep the UPM package and remove the
`Assets/` copy. Check the console after install to catch this.

## Resolve the native dependencies after install

The native SDKs (the `io.bidmachine.plus` Android library and the iOS pod) come through EDM4U, not the
package itself. After the package installs, resolve them so they reach the build:

- **Android:** run **Assets > External Dependency Manager > Android Resolver > Resolve** (or build).
- **iOS:** the **iOS Resolver** installs the pod on the next build.

A project that already runs a mediation has the EDM4U resolvers — and, on Android, the custom Gradle
templates (**Player Settings > Publishing Settings**) — set up already, so this is usually the only
export step. If the Android resolver reports the Gradle templates are off, enable **Custom Main Gradle
Template** and **Custom Gradle Settings Template** and resolve again.
