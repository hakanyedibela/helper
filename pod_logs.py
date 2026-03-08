#!/usr/bin/env python3
"""
Show logs for a Kubernetes pod using a partial name match.
If multiple pods match, an interactive selection menu is shown.

Usage:
    python pod_logs.py <partial-name> [options]

Examples:
    python pod_logs.py nginx
    python pod_logs.py api -f --tail 200
    python pod_logs.py worker -n production
    python pod_logs.py db -A -c postgres
"""

import argparse
import subprocess
import sys


def get_pods(namespace=None, all_namespaces=False):
    cmd = [
        "kubectl", "get", "pods", "--no-headers",
        "-o", "custom-columns=NAME:.metadata.name,NAMESPACE:.metadata.namespace,STATUS:.status.phase"
    ]
    if all_namespaces:
        cmd.append("--all-namespaces")
    elif namespace:
        cmd.extend(["-n", namespace])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] Failed to list pods: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    pods = []
    for line in result.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) >= 3:
            pods.append({"name": parts[0], "namespace": parts[1], "status": parts[2]})
    return pods


def filter_pods(pods, partial_name):
    return [p for p in pods if partial_name.lower() in p["name"].lower()]


def select_pod(pods):
    if len(pods) == 1:
        print(f"[+] Found pod: {pods[0]['name']}  (namespace: {pods[0]['namespace']}, status: {pods[0]['status']})")
        return pods[0]

    print(f"\n[?] Multiple pods match — select one:\n")
    for i, pod in enumerate(pods, 1):
        status_indicator = "[OK]" if pod["status"] == "Running" else f"[{pod['status']}]"
        print(f"  {i}) {pod['name']:<50} ns: {pod['namespace']:<20} {status_indicator}")

    while True:
        try:
            choice = input(f"\nEnter number [1-{len(pods)}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(pods):
                return pods[idx]
            print(f"[!] Please enter a number between 1 and {len(pods)}.")
        except ValueError:
            print("[!] Invalid input. Enter a number.")
        except KeyboardInterrupt:
            print("\n[i] Aborted.")
            sys.exit(0)


def show_logs(pod, container=None, follow=False, tail=100, previous=False):
    cmd = ["kubectl", "logs", pod["name"], "-n", pod["namespace"]]
    if container:
        cmd.extend(["-c", container])
    if follow:
        cmd.append("-f")
    if tail is not None:
        cmd.extend(["--tail", str(tail)])
    if previous:
        cmd.append("-p")

    mode = "streaming" if follow else f"last {tail} lines"
    print(f"\n[*] {pod['name']}  |  ns: {pod['namespace']}  |  {mode}")
    print("-" * 70)

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[i] Log streaming stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Show Kubernetes pod logs using a partial pod name"
    )
    parser.add_argument("name", help="Partial pod name to search for")
    parser.add_argument("-n", "--namespace",
                        help="Kubernetes namespace (default: current context namespace)")
    parser.add_argument("-A", "--all-namespaces", action="store_true",
                        help="Search across all namespaces")
    parser.add_argument("-c", "--container",
                        help="Container name (required for multi-container pods)")
    parser.add_argument("-f", "--follow", action="store_true",
                        help="Stream logs in real time (like kubectl logs -f)")
    parser.add_argument("--tail", type=int, default=100,
                        help="Number of recent log lines to show (default: 100)")
    parser.add_argument("-p", "--previous", action="store_true",
                        help="Show logs from the previous (crashed) container instance")
    args = parser.parse_args()

    pods = get_pods(namespace=args.namespace, all_namespaces=args.all_namespaces)

    if not pods:
        print("[!] No pods found in the current namespace/context.")
        sys.exit(1)

    matches = filter_pods(pods, args.name)

    if not matches:
        print(f"[!] No pods found matching '{args.name}'.\n")
        print("[i] Available pods:")
        for pod in pods:
            print(f"    {pod['name']:<50} ns: {pod['namespace']}")
        sys.exit(1)

    selected = select_pod(matches)
    show_logs(
        selected,
        container=args.container,
        follow=args.follow,
        tail=args.tail,
        previous=args.previous,
    )


if __name__ == "__main__":
    main()
