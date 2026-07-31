# vssctl

> A developer-friendly CLI for managing Vehicle Signal Specification (VSS), generating KUKSA Databroker metadata, and publishing reusable Databroker images.

---

## Why vssctl?

When working with Eclipse KUKSA Databroker, developers typically need to:

* Understand the VSS specification
* Edit `.vspec` files
* Run the VSS generation tools
* Generate metadata JSON
* Build a Databroker image
* Push the image to a container registry

Although each step is straightforward individually, the overall workflow is difficult for application developers who simply want to add a new vehicle signal.

For example, adding one signal may require knowledge of:

* VSS hierarchy
* `.vspec` syntax
* VSS generation tools
* Docker or Podman
* GitHub Container Registry (GHCR)

Most developers should not need to understand all of these technologies.

`vssctl` hides this complexity behind a simple CLI.

Instead of editing VSS manually, developers focus on describing signals, while `vssctl` generates the required artifacts automatically.

---

# Goals

The primary goals of this project are:

* Make VSS easy for developers
* Eliminate manual `.vspec` editing
* Standardize Databroker images across teams
* Produce reproducible builds
* Integrate naturally with CI/CD
* Keep VSS as the single source of truth

---

# Target Users

This project is intended for:

* Automotive software developers
* Middleware teams
* KUKSA Databroker users
* SDV (Software Defined Vehicle) platforms
* CI/CD pipelines
* Integration engineers

---

# Current Problems

Today, a typical workflow looks like this:

```
Developer

↓

Edit .vspec

↓

Run VSS tools

↓

Generate JSON

↓

Build Databroker

↓

Push Image

↓

Team pulls image
```

This workflow has several drawbacks:

* Developers must understand VSS syntax.
* Manual editing introduces mistakes.
* Duplicate signals are common.
* Different developers may generate different outputs.
* CI pipelines become difficult to maintain.

---

# vssctl Workflow

With `vssctl`, the workflow becomes:

```
Developer

↓

vssctl signal add

↓

Validation

↓

Generate VSS

↓

Generate Metadata

↓

Build Databroker

↓

Publish Image

↓

Team pulls image
```

The developer only interacts with the CLI.

Everything else is automated.

---

# Design Principles

## Single Source of Truth

Only one file should be maintained by developers.

```
signals.yaml
```

Everything else is generated.

```
signals.yaml

↓

company.vspec

↓

vss_release_6.0.json

↓

Dockerfile

↓

Databroker Image
```

Generated files should never be edited manually.

---

## Separation of Responsibilities

The project is organized into independent layers.

```
CLI

↓

Services

↓

Repository

↓

Storage

↓

YAML
```

Each layer has a single responsibility.

---

## Extensibility

The storage implementation should be replaceable.

Today:

```
YAML
```

Tomorrow:

* SQLite
* PostgreSQL
* Git Repository
* REST API

The CLI should not need to change.

---

# Project Structure

```
vssctl/

├── src/
│   └── vssctl/
│       ├── commands/
│       ├── core/
│       ├── templates/
│       └── utils/
│
├── workspace/
│   ├── catalog/
│   ├── generated/
│   ├── docker/
│   └── build/
│
├── team_vss/
│
├── tests/
│
└── .github/
```

---

# Repository Layout

## src/

Contains the application source code.

### commands/

CLI commands.

Examples:

* signal
* build
* publish
* validate

---

### core/

Business logic.

Examples:

* Catalog
* Validator
* Tree Builder
* Generator
* Docker Builder

---

### templates/

Templates used to generate:

* Dockerfile
* VSpec
* Metadata

---

### utils/

Shared helper functions.

---

## workspace/

Temporary project workspace.

Developers only interact with the catalog.

```
workspace/

catalog/

generated/

docker/
```

---

## workspace/catalog

Contains the signal catalog.

```
signals.yaml
```

This is the only file that developers modify.

---

## workspace/generated

Generated artifacts.

Examples:

```
company.vspec

vss_release_6.0.json

tree.json
```

Never edit these files manually.

---

## team_vss/

Contains the official VSS baseline used by the team.

Examples:

* VSS 6.0
* Company extensions
* Common definitions

These files should be treated as read-only inputs.

---

# Current Milestone

## Milestone 1

Completed

Features:

* Project bootstrap
* CLI
* Doctor command
* Signal command
* Python packaging

---

## Milestone 2

Completed

Features:

* Signal catalog
* YAML storage
* Catalog service
* Add signal
* Remove signal
* Search signal
* List signal

No VSS generation yet.

---

## Upcoming Milestones

### Milestone 3

Signal validation

* Duplicate detection
* Datatype validation
* Parent validation
* Naming rules

---

### Milestone 4

Tree Builder

Generate an in-memory VSS hierarchy.

---

### Milestone 5

Completed

VSpec & Metadata Generator

Features:
- Automatic generation of `workspace/generated/company.vspec` from custom signals.
- Preparation of merged compilation environment under `workspace/generated/merged/`.
- Execution of the official VSS compiler (`vspec export json`) to compile VSS 6.0 specification and custom signals.
- Programmatic synchronization of all 8 VSS release versions (from 2.0 to 6.0) in `workspace/generated/json_tree/` (adding/updating/removing custom signals while keeping original official baselines intact).

---

### Milestone 7

Docker Builder

Automatically build a Databroker image.

```
podman build

↓

Databroker Image
```

---

### Milestone 8

Smoke Testing

Automatically verify:

* Metadata loads
* Signals exist
* Databroker starts correctly

---

### Milestone 9

GHCR Publisher

Publish versioned images.

Example:

```
ghcr.io/company/databroker:v1.0.0-vss6.0
```

---

### Milestone 10

GitHub Actions

CI will automatically:

* Validate
* Generate
* Build
* Test
* Publish

---

### Milestone 11

Interactive CLI

Instead of typing:

```
Vehicle.ADAS.AutoPilot.Enabled
```

Users browse the hierarchy interactively.

---

### Milestone 12

Web Dashboard

A web interface for:

* Browsing signals
* Editing signals
* Validation
* Building images
* Publishing images

---

# Long-Term Vision

The long-term vision is to make `vssctl` the standard platform for managing VSS in a development team.

Instead of manually editing VSS files, every developer works through the CLI or a future web interface.

The tool becomes responsible for:

* Managing the signal catalog
* Generating valid VSS
* Producing Databroker metadata
* Building standardized Databroker images
* Publishing reusable container images
* Integrating with CI/CD pipelines

This provides a consistent, reproducible, and maintainable workflow for teams adopting Eclipse KUKSA and the Vehicle Signal Specification.

---

# Developer Guide

This section explains how to set up `vssctl` locally, configure default behaviors, enable shell completions, and understand CI/CD pipeline behaviors.

## Local Configuration (`.vssctl.yaml`)

`vssctl` supports loading workspace-wide and developer-specific settings from a configuration file. The tool searches for `.vssctl.yaml` in the following locations (highest priority first):
1. An explicit file path specified by the `--config <path>` global option.
2. The project workspace root directory (`.vssctl.yaml`).
3. The user's home directory (`$HOME/.vssctl.yaml`).

### Example Configuration

Create a file named `.vssctl.yaml` with the following structure:

```yaml
workspace:
  databroker_path: "workspace/databroker"
  output_dir: "workspace/output"
defaults:
  engine: "auto"       # auto | podman | docker
  ghcr_org: "bachvn1711"
  vss_version: "6.0"
```

## Shell Autocompletion

`vssctl` provides native shell tab-completion script generation for `bash`, `zsh`, and `fish`.

### Generation

To generate the completion script for your active shell, run:

```bash
vssctl completion [bash|zsh|fish]
```

### Installation

For **Bash**, add the following line to your `~/.bashrc`:

```bash
eval "$(vssctl completion bash)"
```

For **Zsh**, add the following line to your `~/.zshrc`:

```bash
eval "$(vssctl completion zsh)"
```

For **Fish**, add the following line to your `~/.config/fish/config.fish`:

```fish
vssctl completion fish | source
```

---

## Local Pipeline Workflow

To execute all local compilation steps (validation, spec generation, container assembly, and optional registry publishing) in a single command, use:

```bash
# Run validation, generate JSON, and build Podman/Docker image
vssctl pipeline

# Run the complete sequence and publish directly to GHCR
vssctl pipeline --publish --token <your-github-pat>
```

---

## CI/CD Pipeline & GitHub Actions Workflow

When pushing commits or releases to GitHub, the automated pipeline in `.github/workflows/release.yml` performs the following steps:

1. **Triggers:** Fires on pushes to `main`/`master`, pushes to release version tags (matching `v*.*.*`), or manual dispatches (`workflow_dispatch`).
2. **Testing:** Executes the complete Python `pytest` test suite to check for command correctness and exceptions.
3. **Validation & Generation:** Runs `vssctl validate` to verify VSS specifications, then generates versioned release schemas (`vss_release_6.0.json`).
4. **Publishing (GHCR):** Logs into GHCR, builds the Databroker container using the generated VSS spec, tags it with the branch/tag version, and pushes it to `ghcr.io/bachvn1711/databroker`.
5. **Release Assets:** When a release tag `v*.*.*` is pushed, the workflow creates a new GitHub Release and attaches the generated `vss_release_6.0.json` metadata JSON as download artifacts.

---

# License

Apache License 2.0

---

# Contributing

Contributions are welcome.

Future areas include:

* Additional generators
* More storage backends
* Better validation rules
* Interactive tree navigation
* Web dashboard
* Support for newer VSS releases
