#!/usr/bin/env python3
"""Verify a BidMachine Plus *Android* integration — read-only.

Scans a Gradle project for the dependency, Maven repo, network-security config, SDK
init, and leftover test-mode / placeholder keys. Prints PASS / WARN / FAIL per check
and exits non-zero if any check FAILs. Pure stdlib; never writes or modifies anything.

Usage:
    python3 verify_integration.py /path/to/android/project
"""
import os
import re
import sys

# --- check primitives -------------------------------------------------------
PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
results = []  # (status, label, detail)


def record(status, label, detail=""):
    results.append((status, label, detail))


def walk_files(root, names=None, exts=None, skip_dirs=(".git", "build", ".gradle", "node_modules")):
    """Yield (path, text) for matching files under root."""
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


# --- checks -----------------------------------------------------------------
def check_dependency(root):
    gradle = list(walk_files(root, exts=(".gradle", ".gradle.kts", ".toml")))
    blob = "\n".join(t for _, t in gradle)

    # Accept both the one-string coordinate and the version-catalog forms:
    #   implementation "io.bidmachine.plus:sdk:0.1.0"
    #   libs.versions.toml: module = "io.bidmachine.plus:sdk"  (version.ref separate)
    #   libs.versions.toml: group = "io.bidmachine.plus", name = "sdk"
    ver_m = re.search(r"io\.bidmachine\.plus:sdk:([0-9][\w.\-]*)", blob)
    has_coord = "io.bidmachine.plus:sdk" in blob
    has_split = bool(re.search(r"io\.bidmachine\.plus", blob)
                     and re.search(r'name\s*=\s*["\']sdk["\']', blob))
    if ver_m:
        record(PASS, "BidMachine dependency", f"io.bidmachine.plus:sdk:{ver_m.group(1)}")
    elif has_coord or has_split:
        record(PASS, "BidMachine dependency", "io.bidmachine.plus:sdk declared (version catalog)")
    else:
        record(FAIL, "BidMachine dependency", "no io.bidmachine.plus:sdk found (string or version-catalog form)")

    has_bm_repo = "artifactory.bidmachine.io/bidmachine" in blob
    if has_bm_repo:
        record(PASS, "Maven repo (bidmachine)", "artifactory.bidmachine.io declared")
    else:
        record(WARN, "Maven repo (bidmachine)", "no artifactory.bidmachine.io — SDK must be resolvable from your configured repos")

    if "play-services-ads-identifier" in blob:
        record(PASS, "Ads-identifier dep", "play-services-ads-identifier present")
    else:
        record(WARN, "Ads-identifier dep", "play-services-ads-identifier not found (needed for GAID)")


def check_manifest(root):
    manifests = list(walk_files(root, names=("AndroidManifest.xml",)))
    if not manifests:
        record(WARN, "AndroidManifest", "no AndroidManifest.xml found")
        return
    blob = "\n".join(t for _, t in manifests)
    if "android.permission.INTERNET" in blob:
        record(PASS, "INTERNET permission", "")
    else:
        record(FAIL, "INTERNET permission", "missing <uses-permission INTERNET>")
    if "networkSecurityConfig" in blob:
        record(PASS, "Network security config", "android:networkSecurityConfig referenced")
    else:
        record(WARN, "Network security config", "no networkSecurityConfig (cleartext demand creatives may fail)")


def check_init(root):
    src = list(walk_files(root, exts=(".kt", ".java")))
    inst_re = re.compile(r"BidMachine\.instance\s*\(")
    init_re = re.compile(r"\.initialize\s*\(")
    adnetwork_re = re.compile(r"IntegrationType\.AdNetwork|integrationType\s*=\s*.*AdNetwork", re.I)
    mediation_re = re.compile(r"IntegrationType\.Mediation", re.I)
    mediator_re = re.compile(r"\.withMediator\s*\(")

    has_instance = any(inst_re.search(t) for _, t in src)
    has_initialize = any(init_re.search(t) for _, t in src)
    if has_instance and has_initialize:
        record(PASS, "SDK init", "BidMachine.instance(...).initialize(...) found")
    elif has_instance:
        record(FAIL, "SDK init", "BidMachine.instance(...) found but initialize(...) is missing — the SDK is never initialized")
    else:
        record(FAIL, "SDK init", "no BidMachine.instance(...) call found")

    has_an = any(adnetwork_re.search(t) for _, t in src)
    has_med = any(mediation_re.search(t) for _, t in src)
    has_mediator = any(mediator_re.search(t) for _, t in src)
    # withMediator is analytics-only — it is NEVER a hard failure in any mode.
    if has_an and has_mediator:
        record(PASS, "Init mode", "AdNetwork + withMediator (plugged into 3rd-party mediation — analytics only)")
    elif has_an:
        record(PASS, "Init mode", "AdNetwork (standalone header bidding)")
    elif has_med and has_mediator:
        record(WARN, "Init mode", "Mediation + withMediator — mediator is analytics-only and ignored in Mediation mode; drop it")
    elif has_med:
        record(PASS, "Init mode", "Mediation (BidMachine runs the auction)")
    else:
        record(WARN, "Init mode", "could not detect IntegrationType — verify InitializationConfigBuilder")


def check_release_hygiene(root):
    src = list(walk_files(root, exts=(".kt", ".java")))
    test_re = re.compile(r"withTestModeEnabled\s*\(\s*true|withLoggingEnabled\s*\(\s*true", re.I)
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


# --- main -------------------------------------------------------------------
def main():
    if len(sys.argv) != 2:
        print("usage: verify_integration.py /path/to/android/project", file=sys.stderr)
        return 2
    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    check_dependency(root)
    check_manifest(root)
    check_init(root)
    check_release_hygiene(root)

    icon = {PASS: "✓", WARN: "!", FAIL: "✗"}
    print(f"\nBidMachine Plus — Android integration check  ({root})\n")
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
