# Helper Scripts

A collection of Python utility scripts for Kubernetes and infrastructure management.

## Requirements

| Tool | Purpose |
|------|---------|
| Python 3.6+ | Run all scripts |
| `kubectl` | Required for Kubernetes scripts |
| `scp` / OpenSSH | Required for scripts that access remote servers |

> SSH key-based authentication is strongly recommended. See [SSH Setup](#ssh-setup) at the bottom.

---

## Scripts

| Script | Description |
|--------|-------------|
| [copy_kubeconfig.py](#copy_kubeconfigpy) | Copy and merge a kubeconfig from a remote server |
| [pod_logs.py](#pod_logspy) | View pod logs using a partial pod name |
| [describe_crd.py](#describe_crdpy) | Describe Kubernetes CRDs using a partial name |

---

## copy_kubeconfig.py

Copies a kubeconfig file from a remote Kubernetes server and merges it into your local `~/.kube/config`.

**Features:**
- Copies via `scp` — no extra Python dependencies
- Backs up your existing config before any changes
- Merges contexts without overwriting existing ones
- Prints all available contexts after the merge

### Usage

```bash
python copy_kubeconfig.py <host> [options]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `host` | Remote server hostname or IP | *(required)* |
| `-u`, `--user` | SSH user | `root` |
| `-p`, `--port` | SSH port | `22` |
| `-r`, `--remote-path` | Kubeconfig path on remote server | `/etc/kubernetes/admin.conf` |
| `-l`, `--local-config` | Local kubeconfig to merge into | `~/.kube/config` |

```bash
# Basic usage
python copy_kubeconfig.py 192.168.1.10

# Custom user and port
python copy_kubeconfig.py k8s-master -u ubuntu -p 2222

# Remote kubeconfig at a non-default path
python copy_kubeconfig.py k8s-master -r ~/.kube/config

# Merge into a different local file
python copy_kubeconfig.py 192.168.1.10 -l ~/.kube/cluster2.yaml
```

### How It Works

1. Downloads the remote kubeconfig to a temp file via `scp`
2. If no local config exists — saves it directly to `~/.kube/config`
3. If a local config exists:
   - Creates a backup at `~/.kube/config.bak`
   - Merges both configs using `kubectl config view --flatten`
   - Writes the merged result back and sets permissions to `600`
4. Cleans up the temp file automatically

### Backup & Recovery

```bash
# Restore from backup
cp ~/.kube/config.bak ~/.kube/config
```

### Switching Contexts

```bash
kubectl config get-contexts                    # list all contexts
kubectl config use-context <context-name>      # switch context
kubectl config current-context                 # show active context
```

---

## pod_logs.py

View logs for a Kubernetes pod using a partial name match — no need to type the full pod name.
If multiple pods match, an interactive selection menu is shown.

**Features:**
- Partial name matching (case-insensitive)
- Interactive numbered menu when multiple pods match
- Supports all common `kubectl logs` options
- Shows all available pods if no match is found

### Usage

```bash
python pod_logs.py <partial-name> [options]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `name` | Partial pod name to search for | *(required)* |
| `-n`, `--namespace` | Kubernetes namespace | current context |
| `-A`, `--all-namespaces` | Search across all namespaces | `false` |
| `-c`, `--container` | Container name (multi-container pods) | — |
| `-f`, `--follow` | Stream logs in real time | `false` |
| `--tail` | Number of recent log lines to show | `100` |
| `-p`, `--previous` | Show logs from previous (crashed) container | `false` |

```bash
# Show last 100 lines for any pod containing "nginx"
python pod_logs.py nginx

# Stream logs in real time
python pod_logs.py api -f

# Last 500 lines in a specific namespace
python pod_logs.py worker -n production --tail 500

# Search across all namespaces
python pod_logs.py db -A

# Specify container in a multi-container pod
python pod_logs.py db -c postgres

# Logs from a previously crashed container
python pod_logs.py app -p
```

### Example — Multiple Matches

```
[?] Multiple pods match — select one:

  1) api-deployment-6d4f8b-xkqzp     ns: default       [OK]
  2) api-deployment-6d4f8b-wmnbr     ns: default       [OK]
  3) api-worker-7c9d5f-plrtk         ns: production    [OK]

Enter number [1-3]: 1

[*] api-deployment-6d4f8b-xkqzp  |  ns: default  |  last 100 lines
----------------------------------------------------------------------
...logs...
```

---

## describe_crd.py

Describe Kubernetes CRDs (Custom Resource Definitions) using a partial name match.
If multiple CRDs match, an interactive selection menu is shown.

**Features:**
- Partial name matching (case-insensitive)
- Interactive numbered menu when multiple CRDs match
- Output as plain `describe`, `yaml`, or `json`
- Human-readable schema summary with `--show-schema`
- `--list` flag to browse all installed CRDs

### Usage

```bash
python describe_crd.py <partial-name> [options]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `name` | Partial CRD name to search for | *(omit to list all)* |
| `-o`, `--output` | Output format: `yaml` or `json` | `describe` |
| `--show-schema` | Print a human-readable schema summary | `false` |
| `--list` | List all available CRDs and exit | `false` |

```bash
# Describe a CRD by partial name
python describe_crd.py kafka

# Get the full CRD definition as YAML
python describe_crd.py cert -o yaml

# Show a readable summary of the CRD schema
python describe_crd.py prometheus --show-schema

# List all CRDs installed in the cluster
python describe_crd.py --list
```

### Example — Multiple Matches

```
[?] Multiple CRDs match — select one:

  1) kafkas.kafka.strimzi.io           group: kafka.strimzi.io    scope: Namespaced
  2) kafkaconnects.kafka.strimzi.io    group: kafka.strimzi.io    scope: Namespaced
  3) kafkatopics.kafka.strimzi.io      group: kafka.strimzi.io    scope: Namespaced

Enter number [1-3]: 1

[*] Describing CRD: kafkas.kafka.strimzi.io
----------------------------------------------------------------------
Name:         kafkas.kafka.strimzi.io
...
```

### Example — Schema Summary

```
[*] Schema for CRD: prometheuses.monitoring.coreos.com
----------------------------------------------------------------------

Version: v1  (served=True, storage=True)
  - spec (object)
      - replicas (integer): Number of desired Prometheus instances
      - retention (string): How long to retain samples in storage
      - resources (object): Resource requirements
      ...
```

---

## SSH Setup

If you haven't configured key-based SSH access yet:

```bash
# Generate a key pair
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy your public key to the remote server
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@your-server
```
