# copy_kubeconfig.py

A Python script to copy a kubeconfig file from a remote Kubernetes server and merge it into your local `~/.kube/config`.

## Features

- Copies the kubeconfig from a remote server via `scp`
- Automatically backs up your existing local config before any changes
- Merges the remote config into your local one (preserving all existing contexts)
- Displays available contexts after a successful merge
- No third-party Python dependencies required

## Requirements

| Tool | Purpose |
|------|---------|
| Python 3.6+ | Run the script |
| `scp` / OpenSSH | Copy the file from the remote server |
| `kubectl` | Merge kubeconfig files |

> SSH key-based authentication is strongly recommended over password auth.

## Usage

```bash
python copy_kubeconfig.py <host> [options]
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `host` | Remote server hostname or IP address | *(required)* |
| `-u`, `--user` | SSH user | `root` |
| `-p`, `--port` | SSH port | `22` |
| `-r`, `--remote-path` | Path to kubeconfig on the remote server | `/etc/kubernetes/admin.conf` |
| `-l`, `--local-config` | Local kubeconfig file to merge into | `~/.kube/config` |

### Examples

```bash
# Minimal — connect as root on port 22
python copy_kubeconfig.py 192.168.1.10

# Custom SSH user and port
python copy_kubeconfig.py k8s-master -u ubuntu -p 2222

# Remote kubeconfig at a non-default path
python copy_kubeconfig.py k8s-master -r ~/.kube/config

# Merge into a different local file
python copy_kubeconfig.py 192.168.1.10 -l ~/.kube/cluster2.yaml
```

## How It Works

1. Connects to the remote server via `scp` and downloads the kubeconfig to a temporary file.
2. If no local config exists, saves the file directly to `~/.kube/config`.
3. If a local config already exists:
   - Creates a backup at `~/.kube/config.bak`
   - Merges both configs using `kubectl config view --flatten` via the `KUBECONFIG` env var trick
   - Writes the merged result back to `~/.kube/config`
4. Prints all available contexts after the merge.
5. Cleans up the temporary file automatically.

## Backup & Recovery

Before every merge, a backup is saved automatically:

```
~/.kube/config.bak
```

To restore it:

```bash
cp ~/.kube/config.bak ~/.kube/config
```

## Setting Up SSH Key Authentication

If you haven't already set up key-based SSH access to your server:

```bash
# Generate a key pair (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy your public key to the remote server
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@your-server
```

## Switching Between Contexts

After merging, use standard `kubectl` commands to manage contexts:

```bash
# List all contexts
kubectl config get-contexts

# Switch to a specific context
kubectl config use-context <context-name>

# Show current context
kubectl config current-context
```
