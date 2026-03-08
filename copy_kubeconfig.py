#!/usr/bin/env python3
"""
Copy and merge a kubeconfig from a remote server into ~/.kube/config.

Usage:
    python copy_kubeconfig.py <host> [options]

Examples:
    python copy_kubeconfig.py 192.168.1.10
    python copy_kubeconfig.py k8s-master -u ubuntu -p 2222
    python copy_kubeconfig.py k8s-master -r ~/.kube/config
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def scp_copy(user: str, host: str, port: int, remote_path: str, local_path: str):
    cmd = ["scp", "-P", str(port), "-o", "StrictHostKeyChecking=no",
           f"{user}@{host}:{remote_path}", local_path]
    print(f"[*] Copying {user}@{host}:{remote_path} ...")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("[!] scp failed. Make sure SSH access is configured correctly.", file=sys.stderr)
        sys.exit(1)


def merge_kubeconfigs(existing: str, new_config: str):
    local_config = Path(existing).expanduser().resolve()

    # No existing config — just copy
    if not local_config.exists():
        local_config.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(new_config, local_config)
        os.chmod(local_config, 0o600)
        print(f"[+] No existing config found. Saved to {local_config}")
        return

    # Backup existing config
    backup = str(local_config) + ".bak"
    shutil.copy(local_config, backup)
    print(f"[*] Backup saved to {backup}")

    # Merge using the KUBECONFIG env var trick + kubectl flatten
    env = os.environ.copy()
    env["KUBECONFIG"] = f"{local_config}:{new_config}"

    result = subprocess.run(
        ["kubectl", "config", "view", "--flatten"],
        capture_output=True, text=True, env=env
    )

    if result.returncode != 0:
        print("[!] kubectl merge failed. Is kubectl installed?", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        print(f"[i] Remote config saved at {new_config} — merge it manually.", file=sys.stderr)
        sys.exit(1)

    with open(local_config, "w") as f:
        f.write(result.stdout)
    os.chmod(local_config, 0o600)
    print(f"[+] Merged successfully into {local_config}")

    # Show resulting contexts
    ctx_result = subprocess.run(
        ["kubectl", "config", "get-contexts", "--no-headers"],
        capture_output=True, text=True
    )
    if ctx_result.returncode == 0:
        print("\n[i] Available contexts after merge:")
        print(ctx_result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(
        description="Copy and merge kubeconfig from a remote server into ~/.kube/config"
    )
    parser.add_argument("host", help="Remote server hostname or IP address")
    parser.add_argument("-u", "--user", default="root",
                        help="SSH user (default: root)")
    parser.add_argument("-p", "--port", default=22, type=int,
                        help="SSH port (default: 22)")
    parser.add_argument("-r", "--remote-path", default="/etc/kubernetes/admin.conf",
                        help="Remote kubeconfig path (default: /etc/kubernetes/admin.conf)")
    parser.add_argument("-l", "--local-config", default="~/.kube/config",
                        help="Local kubeconfig to merge into (default: ~/.kube/config)")
    args = parser.parse_args()

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        scp_copy(args.user, args.host, args.port, args.remote_path, tmp_path)
        merge_kubeconfigs(args.local_config, tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    main()
