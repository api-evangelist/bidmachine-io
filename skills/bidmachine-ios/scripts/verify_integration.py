#!/usr/bin/env python3
"""Verify a BidMachine Plus *iOS* integration — read-only.

Scans an Xcode/CocoaPods/SPM project for the BidMachine dependency, Info.plist keys
(ATS, SKAdNetwork, ATT), SDK init, and leftover test-mode / placeholder keys. Prints
PASS / WARN / FAIL per check and exits non-zero if any check FAILs. Pure stdlib;
never writes or modifies anything.

Usage:
    python3 verify_integration.py /path/to/ios/project
"""
import os
import re
import sys

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
results = []


def record(status, label, detail=""):
    results.append((status, label, detail))


def walk_files(root, names=None, exts=None, skip_dirs=(".git", "Pods", "build", "DerivedData", "node_modules")):
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


def check_dependency(root):
    pods = list(walk_files(root, names=("Podfile",)))
    # The Plus coordinate is `BidMachinePlus` (CocoaPods) / `BidMachinePlus-SPM` (SPM) — the only
    # names accepted here (coordinate list: skills/bidmachine-ios/references/distribution.md). The
    # classic `BidMachine` / `BidMachine-SPM` pods are a different product, not Plus, so they are
    # intentionally not matched. An optional `/Subspec` (e.g. `BidMachinePlus/Static`) is allowed.
    # These patterns match by NAME, so they're stable across distribution-source changes;
    # only update them if the package names themselves change.
    pod_re = re.compile(r"pod\s+['\"](BidMachinePlus)(?:/\w+)?['\"]")
    spm_re = re.compile(r"BidMachinePlus-SPM")
    objc_re = re.compile(r"-ObjC")

    spm_files = list(walk_files(root, names=("Package.swift", "Package.resolved")))
    pbxproj = list(walk_files(root, exts=(".pbxproj",)))
    spm_blob = "\n".join(t for _, t in spm_files) + "\n".join(t for _, t in pbxproj)

    pod_hit = None
    for _, t in pods:
        m = pod_re.search(t)
        if m:
            pod_hit = m.group(1)
            break
    spm_hit = spm_re.search(spm_blob)
    if pod_hit:
        record(PASS, "BidMachine dependency", f"pod '{pod_hit}' in Podfile")
    elif spm_hit:
        record(PASS, "BidMachine dependency", f"{spm_hit.group(0)} package referenced")
    else:
        record(FAIL, "BidMachine dependency",
               "no BidMachine Plus dependency found — expected the 'BidMachinePlus' CocoaPods "
               "pod or the 'BidMachinePlus-SPM' Swift package")

    # -ObjC linker flag (required for category symbols)
    flag_blob = "\n".join(t for _, t in pbxproj) + "\n".join(t for _, t in pods)
    if objc_re.search(flag_blob):
        record(PASS, "-ObjC linker flag", "present")
    else:
        record(WARN, "-ObjC linker flag", "OTHER_LDFLAGS -ObjC not detected (required for SPM/static builds)")


def check_plist(root):
    plists = list(walk_files(root, names=("Info.plist",)))
    if not plists:
        record(WARN, "Info.plist", "no Info.plist found (may be generated)")
        return
    blob = "\n".join(t for _, t in plists)
    if "NSAppTransportSecurity" in blob:
        record(PASS, "App Transport Security", "NSAppTransportSecurity present")
    else:
        record(WARN, "App Transport Security", "NSAppTransportSecurity not set (some creatives may fail)")
    if "SKAdNetworkItems" in blob:
        record(PASS, "SKAdNetwork", "SKAdNetworkItems present")
    else:
        record(WARN, "SKAdNetwork", "SKAdNetworkItems missing (attribution on iOS 14+)")
    if "NSUserTrackingUsageDescription" in blob:
        record(PASS, "ATT usage string", "NSUserTrackingUsageDescription present")
    else:
        record(WARN, "ATT usage string", "NSUserTrackingUsageDescription missing (needed for IDFA)")


def check_init(root):
    src = list(walk_files(root, exts=(".swift", ".m", ".mm")))
    instance_re = re.compile(r"BidMachine\.instance\s*\(|\[BidMachine\s+instanceWithAppKey")
    initialize_re = re.compile(r"\.initialize\s*\(|initializeWithConfig", re.I)
    adnetwork_re = re.compile(r"integrationType:\s*\.adNetwork|\.adNetwork", re.I)
    mediation_re = re.compile(r"integrationType:\s*\.mediation|\.mediation", re.I)
    mediator_re = re.compile(r"\.with\s*\(\s*mediator:")

    # Both the instance and the initialize call are required — an instance that is never
    # initialized does nothing, so check for both.
    has_instance = any(instance_re.search(t) for _, t in src)
    has_initialize = any(initialize_re.search(t) for _, t in src)
    if has_instance and has_initialize:
        record(PASS, "SDK init", "BidMachine.instance(appKey:) + initialize(config:) found")
    elif has_instance:
        record(FAIL, "SDK init", "BidMachine.instance(...) found but initialize(config:) is missing — the SDK is never initialized")
    else:
        record(FAIL, "SDK init", "no BidMachine.instance(appKey:) call found")

    has_an = any(adnetwork_re.search(t) for _, t in src)
    has_med = any(mediation_re.search(t) for _, t in src)
    has_mediator = any(mediator_re.search(t) for _, t in src)
    # with(mediator:) is analytics-only — it is NEVER a hard failure in any mode.
    if has_an and has_mediator:
        record(PASS, "Mode", "adNetwork + with(mediator:) (plugged into 3rd-party mediation — analytics only)")
    elif has_an:
        record(PASS, "Mode", "adNetwork (standalone header bidding)")
    elif has_med and has_mediator:
        record(WARN, "Mode", "mediation + with(mediator:) — mediator is analytics-only and ignored in .mediation mode; drop it")
    elif has_med:
        record(PASS, "Mode", "mediation (BidMachine runs the auction)")
    else:
        record(WARN, "Mode", "could not detect integrationType — verify InitializationConfigBuilder")


def check_release_hygiene(root):
    src = list(walk_files(root, exts=(".swift", ".m", ".mm")))
    test_re = re.compile(r"testModeEnabled:\s*true|loggingEnabled:\s*true", re.I)
    ph_re = re.compile(r"YOUR_APP_KEY|YOUR_PLACEMENT_ID")
    test_hits = [rel(root, p) for p, t in src if test_re.search(t)]
    ph_hits = [rel(root, p) for p, t in src if ph_re.search(t)]
    if test_hits:
        record(WARN, "Test/logging mode", "enabled in: " + ", ".join(sorted(set(test_hits))) + " — strip before release")
    else:
        record(PASS, "Test/logging mode", "no test/logging mode left enabled")
    if ph_hits:
        record(FAIL, "Placeholder keys", "YOUR_APP_KEY / YOUR_PLACEMENT_ID still in: " + ", ".join(sorted(set(ph_hits))))
    else:
        record(PASS, "Placeholder keys", "no placeholder keys")


def main():
    if len(sys.argv) != 2:
        print("usage: verify_integration.py /path/to/ios/project", file=sys.stderr)
        return 2
    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    check_dependency(root)
    check_plist(root)
    check_init(root)
    check_release_hygiene(root)

    icon = {PASS: "✓", WARN: "!", FAIL: "✗"}
    print(f"\nBidMachine Plus — iOS integration check  ({root})\n")
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
