#!/usr/bin/env python3
"""
Describe Kubernetes CRDs (Custom Resource Definitions) using a partial name match.
If multiple CRDs match, an interactive selection menu is shown.

Usage:
    python describe_crd.py <partial-name> [options]

Examples:
    python describe_crd.py kafka
    python describe_crd.py cert --show-schema
    python describe_crd.py prometheus -o yaml
"""

import argparse
import json
import subprocess
import sys


def run_kubectl(args, capture=True):
    cmd = ["kubectl"] + args
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if result.returncode != 0:
        print(f"[!] kubectl error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip() if capture else None


def get_crds():
    output = run_kubectl([
        "get", "crds", "--no-headers",
        "-o", "custom-columns=NAME:.metadata.name,GROUP:.spec.group,SCOPE:.spec.scope"
    ])
    if not output:
        print("[!] No CRDs found in the cluster.")
        sys.exit(0)

    crds = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            crds.append({"name": parts[0], "group": parts[1], "scope": parts[2]})
    return crds


def filter_crds(crds, partial_name):
    return [c for c in crds if partial_name.lower() in c["name"].lower()]


def select_crd(crds):
    if len(crds) == 1:
        print(f"[+] Found CRD: {crds[0]['name']}")
        return crds[0]

    print(f"\n[?] Multiple CRDs match — select one:\n")
    for i, crd in enumerate(crds, 1):
        print(f"  {i}) {crd['name']:<60} group: {crd['group']:<30} scope: {crd['scope']}")

    while True:
        try:
            choice = input(f"\nEnter number [1-{len(crds)}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(crds):
                return crds[idx]
            print(f"[!] Please enter a number between 1 and {len(crds)}.")
        except ValueError:
            print("[!] Invalid input. Enter a number.")
        except KeyboardInterrupt:
            print("\n[i] Aborted.")
            sys.exit(0)


def describe_crd(name, output_format=None):
    print(f"\n[*] Describing CRD: {name}")
    print("-" * 70)

    if output_format in ("yaml", "json"):
        run_kubectl(["get", "crd", name, "-o", output_format], capture=False)
        return

    # Default: kubectl describe
    run_kubectl(["describe", "crd", name], capture=False)


def show_schema(name):
    print(f"\n[*] Schema for CRD: {name}")
    print("-" * 70)

    raw = run_kubectl(["get", "crd", name, "-o", "json"])
    try:
        crd = json.loads(raw)
    except json.JSONDecodeError:
        print("[!] Failed to parse CRD JSON.", file=sys.stderr)
        sys.exit(1)

    versions = crd.get("spec", {}).get("versions", [])
    if not versions:
        print("[i] No versioned schema found.")
        return

    for version in versions:
        ver_name = version.get("name", "unknown")
        served = version.get("served", False)
        storage = version.get("storage", False)
        schema = version.get("schema", {}).get("openAPIV3Schema", {})

        print(f"\nVersion: {ver_name}  (served={served}, storage={storage})")
        print_schema_node(schema.get("properties", {}), indent=2)


def print_schema_node(properties, indent=0):
    if not properties:
        return
    pad = " " * indent
    for field, meta in properties.items():
        field_type = meta.get("type", "object")
        description = meta.get("description", "")
        desc_short = (description[:60] + "...") if len(description) > 60 else description
        print(f"{pad}- {field} ({field_type})" + (f": {desc_short}" if desc_short else ""))
        nested = meta.get("properties", {})
        if nested:
            print_schema_node(nested, indent + 4)


def list_all_crds(crds):
    print("\n[i] Available CRDs:\n")
    for crd in crds:
        print(f"  {crd['name']:<60} group: {crd['group']:<30} scope: {crd['scope']}")


def main():
    parser = argparse.ArgumentParser(
        description="Describe Kubernetes CRDs using a partial name match"
    )
    parser.add_argument("name", nargs="?",
                        help="Partial CRD name to search for (omit to list all CRDs)")
    parser.add_argument("-o", "--output", choices=["yaml", "json"],
                        help="Output format: yaml or json (instead of describe)")
    parser.add_argument("--show-schema", action="store_true",
                        help="Print a human-readable summary of the CRD schema")
    parser.add_argument("--list", action="store_true",
                        help="List all available CRDs and exit")
    args = parser.parse_args()

    crds = get_crds()

    if args.list or not args.name:
        list_all_crds(crds)
        sys.exit(0)

    matches = filter_crds(crds, args.name)

    if not matches:
        print(f"[!] No CRDs found matching '{args.name}'.\n")
        list_all_crds(crds)
        sys.exit(1)

    selected = select_crd(matches)

    if args.show_schema:
        show_schema(selected["name"])
    else:
        describe_crd(selected["name"], output_format=args.output)


if __name__ == "__main__":
    main()
