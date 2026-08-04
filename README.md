# vssctl

> **A developer-friendly CLI for managing Vehicle Signal Specification (VSS), compiling KUKSA Databroker metadata, and publishing customized Databroker container images.**

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Eclipse KUKSA](https://img.shields.io/badge/Eclipse-KUKSA%20Databroker-orange.svg)](https://github.com/eclipse-kuksa/kuksa-databroker)
[![CI/CD Pipeline](https://github.com/bachvn1711/vsctl/actions/workflows/release.yml/badge.svg)](https://github.com/bachvn1711/vsctl/actions)

---

## Why vssctl?

When deploying KUKSA Databroker inside Software Defined Vehicle (SDV) architectures, adding custom vehicle signals typically requires deep knowledge of:
* VSS specification hierarchy and YAML/vspec formatting rules.
* The official `vspec` compiler compiler arguments.
* Building Rust binaries and composing Docker/Podman container contexts.
* Managing logins and tagging structures for the GitHub Container Registry (GHCR).

`vssctl` hides all this complexity behind a simple CLI command. Developers focus on defining custom properties in a single catalog, while the tool handles compilation, binary compilation, containerization, and publishing.

### Workflow Comparison

```
[Traditional VSS Workflow]
Developer ──> Edit .vspec ──> Run vspec-compiler ──> Generate JSON ──> Compile Rust Databroker ──> Push to GHCR

[The vssctl Workflow]
Developer ──> vssctl signal add ──> vssctl pipeline (Validate, Generate, Build, Publish)
```

---

## Core Features

- **Single Source of Truth:** Manage custom signals in a simple [`signals.yaml`](file:///d:/Work/CODE/AUTONXT_AI/vsctl/workspace/catalog/signals.yaml) catalog.
- **Overlay & Version Compilation:** Automates creating overlay vspecs, running the official VSS compiler, and synchronizing custom signals across **8 legacy VSS versions (v2.0 up to v6.0)**.
- **Smart Container Builder:** Automates generating optimized multi-stage container files. Uses local Rust pre-compiled binary fast-paths if present, or automatically falls back to secure compilations inside the container.
- **One-Command Dev Pipeline:** The `vssctl pipeline` subcommand runs validation, schema compilation, container packaging, and image publishing sequentially.
- **Pre-flight Doctors & Environment Checking:** Quickly validates Python versions, compiler paths, and active Podman/Docker runtimes.
- **CI/CD Release Automation:** A pre-configured GitHub Actions pipeline compiles assets, runs tests, publishes to GHCR, and attaches JSON schema releases.

---

## Quick Start

### 1. Installation

Set up a Python virtual environment and install `vssctl` in editable mode:

```bash
# Create and activate environment
python -m venv .venv_win
source .venv_win/Scripts/activate  # Or .venv_win\Scripts\activate on Windows

# Install packages
pip install --upgrade pip
pip install -e .
```

Verify your local installation:
```bash
vssctl doctor
```

### 2. Configure defaults

Create a local configuration file named `.vssctl.yaml` in your project root:

```yaml
workspace:
  databroker_path: "workspace/databroker"
  output_dir: "workspace/output"
defaults:
  engine: "auto"       # auto | podman | docker
  ghcr_org: "bachvn1711"
  vss_version: "6.0"
```

### 3. Add a Custom Signal

Add a custom speed sensor or HVAC control using:
```bash
vssctl signal add
```
This automatically appends a schema-valid signal declaration into `workspace/catalog/signals.yaml`.

### 4. Execute the Build Pipeline

Validate your catalog, compile VSS metadata outputs, and build a local Databroker container:
```bash
vssctl pipeline
```
To build and push directly to GitHub Container Registry under your organization:
```bash
vssctl pipeline --publish --token <your-github-pat>
```

---

## Local Testing

To safely exercise signal management, validation, VSS generation, the terminal UI, and the automated test suite, follow the **[Local Testing Guide](local_test_guide.md)**. It uses an isolated copy so local test data does not alter your working catalog or generated files.

---

## Detailed Documentation & Guides

- **[Local Testing Guide](local_test_guide.md):** Safe manual and automated local verification.
- **[vssctl Handbook](handbook.md):** Architecture, configuration, commands, and troubleshooting.

---

## Roadmap & Status

- [x] **Milestone 1-2:** CLI Core, Catalog Storage (YAML), Signal Management.
- [x] **Milestone 3-4:** Signal Validation Rules, Tree Node Hierarchy Builder.
- [x] **Milestone 5:** Overlay Generator, Multi-release Synchronization (VSS 2.0 to 6.0).
- [x] **Milestone 7:** Container Image Builder (Docker/Podman, Cargo Fast-paths).
- [x] **Milestone 8:** GHCR Image Publisher (`vssctl publish` with stdin secrets).
- [x] **Milestone 9:** Workspace Configuration Files (`.vssctl.yaml`), Shell completions.
- [x] **Milestone 10:** GitHub Actions CI/CD Pipeline (`.github/workflows/release.yml`).
- [ ] **Milestone 11:** Interactive TUI Tree Browser.
- [ ] **Milestone 12:** Web Dashboard UI.

---

## License

Distributed under the Apache License 2.0. See `LICENSE` for details.
