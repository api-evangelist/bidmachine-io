#!/usr/bin/env python3
"""Verify a BidMachine Plus *Unity First Look* integration — read-only.

Scans a Unity project for the BidMachine scoped registry, the com.bidmachine.plus package, External
Dependency Manager (resolved in packages-lock.json, and any duplicate under Assets/), the
Mediation-mode init, a BidMachine fullscreen ad, and leftover placeholders. Prints PASS / WARN / FAIL
per check and exits non-zero if any check FAILs. Pure stdlib; never writes or modifies anything.

This is a static sanity net, not a logic check: it confirms the pieces are present, not that the
First Look fall-through is wired correctly. That correctness comes from compilation and, when it
breaks, the bidmachine-unity-guide agent.

Usage:
    python3 verify_integration.py /path/to/unity/project
"""
import os
import re
import sys

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
results = []


def record(status, label, detail=""):
    results.append((status, label, detail))


def walk_files(root, names=None, exts=None, skip_dirs=(".git", "Library", "Temp", "obj", "Build", "node_modules")):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            if names and fn not in names:
                continue
            if exts and not fn.endswith(tuple(exts)):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    yield path, f.read()
            except OSError:
                continue


def rel(root, path):
    return os.path.relpath(path, root)


def edm_under_assets(root):
    assets = os.path.join(root, "Assets")
    if not os.path.isdir(assets):
        return False
    for dirpath, dirnames, _ in os.walk(assets):
        dirnames[:] = [d for d in dirnames if d not in (".git",)]
        for d in dirnames:
            if d in ("ExternalDependencyManager", "PlayServicesResolver"):
                return True
    return False


def check_registries_and_package(root):
    manifests = list(walk_files(root, names=("manifest.json",)))
    manifest_blob = "\n".join(t for _, t in manifests)
    locks = list(walk_files(root, names=("packages-lock.json",)))
    lock_blob = "\n".join(t for _, t in locks)

    # BidMachine package (a direct dependency, so it lives in manifest.json)
    if re.search(r'"com\.bidmachine\.plus"', manifest_blob):
        record(PASS, "BidMachine package", "com.bidmachine.plus in manifest.json dependencies")
    else:
        any_bmp = any(re.search(r"BidMachineInc\.Plus", t) for _, t in walk_files(root, exts=(".cs",)))
        if any_bmp:
            record(WARN, "BidMachine package", "no com.bidmachine.plus in manifest.json, but BidMachine C# found — embedded?")
        else:
            record(FAIL, "BidMachine package", "no com.bidmachine.plus dependency in any manifest.json")

    # BidMachine scoped registry
    if "npm.bidmachine.com" in manifest_blob or re.search(r'"com\.bidmachine"', manifest_blob):
        record(PASS, "BidMachine registry", "BidMachine scoped registry present")
    else:
        record(WARN, "BidMachine registry", "no BidMachine scoped registry (npm.bidmachine.com / scope com.bidmachine)")

    # EDM4U — check the RESOLVED graph (packages-lock.json), not manifest.json: EDM4U is usually a
    # transitive dependency of com.bidmachine.plus, so it is absent from manifest.json's direct
    # dependencies but present in packages-lock.json.
    edm_resolved = "com.google.external-dependency-manager" in lock_blob
    edm_assets = edm_under_assets(root)
    if edm_resolved and edm_assets:
        record(WARN, "External Dependency Manager", "resolved as a package AND copied under Assets/ — remove the Assets/ copy to avoid duplicate assemblies")
    elif edm_resolved:
        record(PASS, "External Dependency Manager", "resolved in packages-lock.json (direct or transitive)")
    elif edm_assets:
        record(WARN, "External Dependency Manager", "only under Assets/ (manual import) — prefer the UPM package so it resolves through a registry")
    elif not locks:
        record(WARN, "External Dependency Manager", "no packages-lock.json to confirm resolution — ensure a registry serves com.google.external-dependency-manager (e.g. OpenUPM)")
    else:
        record(WARN, "External Dependency Manager", "not in the resolved graph — add a registry that serves com.google.external-dependency-manager (e.g. OpenUPM)")


def check_init(root):
    src = list(walk_files(root, exts=(".cs",)))
    get_instance = any(re.search(r"BidMachine\.GetInstance\s*\(", t) for _, t in src)
    initialize = any(re.search(r"\.Initialize\s*\(", t) for _, t in src)
    mediation = any(re.search(r"IntegrationMode\.Mediation", t) for _, t in src)
    adnetwork = any(re.search(r"IntegrationMode\.AdNetwork", t) for _, t in src)

    if get_instance and initialize:
        record(PASS, "SDK init", "BidMachine.GetInstance(...) + Initialize(config) found")
    else:
        record(FAIL, "SDK init", "no BidMachine.GetInstance(...) + Initialize(...) found")

    if mediation:
        record(PASS, "Mode", "IntegrationMode.Mediation (First Look runs BidMachine as the pre-bid)")
    elif adnetwork:
        record(WARN, "Mode", "IntegrationMode.AdNetwork found — First Look expects IntegrationMode.Mediation")
    else:
        record(WARN, "Mode", "could not detect IntegrationMode — confirm InitializationConfigBuilder(IntegrationMode.Mediation)")


def check_first_look_wiring(root):
    # Only the reliably-detectable part: a BidMachine fullscreen ad is constructed (these are fixed
    # API type names). The fall-through logic — timeout, hand-off, guard, reload — uses
    # project-chosen names and control flow that a static scan cannot verify, so it is left to
    # compilation and the bidmachine-unity-guide agent rather than guessed at here.
    src = list(walk_files(root, exts=(".cs",)))
    bmp_ad = any(re.search(r"new\s+(Interstitial|Rewarded)Ad\s*\(", t) for _, t in src)
    if bmp_ad:
        record(PASS, "First Look — BidMachine ad", "InterstitialAd/RewardedAd constructed (BidMachine requested first)")
    else:
        record(FAIL, "First Look — BidMachine ad", "no InterstitialAd/RewardedAd constructed; BidMachine is never requested first")


def check_release_hygiene(root):
    src = list(walk_files(root, exts=(".cs",)))
    test_re = re.compile(r"WithTestModeEnabled\s*\(\s*true\s*\)|WithLoggingEnabled\s*\(\s*true\s*\)")
    ph_re = re.compile(r"YOUR_[A-Z0-9_]+")
    test_hits = [rel(root, p) for p, t in src if test_re.search(t)]
    ph_hits = [rel(root, p) for p, t in src if ph_re.search(t)]
    if test_hits:
        record(WARN, "Test/logging mode", "literal true in: " + ", ".join(sorted(set(test_hits))) + " — gate on Debug.isDebugBuild so it is off in release")
    else:
        record(PASS, "Test/logging mode", "no literal test/logging mode enabled (gated or off)")
    if ph_hits:
        record(FAIL, "Placeholder keys", "YOUR_… placeholders still in: " + ", ".join(sorted(set(ph_hits))))
    else:
        record(PASS, "Placeholder keys", "no placeholder keys")


def main():
    if len(sys.argv) != 2:
        print("usage: verify_integration.py /path/to/unity/project", file=sys.stderr)
        return 2
    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    check_registries_and_package(root)
    check_init(root)
    check_first_look_wiring(root)
    check_release_hygiene(root)

    icon = {PASS: "✓", WARN: "!", FAIL: "✗"}
    print(f"\nBidMachine Plus — Unity First Look check  ({root})\n")
    for status, label, detail in results:
        line = f"  [{icon[status]}] {status:4} {label}"
        if detail:
            line += f" — {detail}"
        print(line)

    n_fail = sum(1 for s, _, _ in results if s == FAIL)
    n_warn = sum(1 for s, _, _ in results if s == WARN)
    print(f"\n{n_fail} fail, {n_warn} warn, {len(results)} checks total.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
