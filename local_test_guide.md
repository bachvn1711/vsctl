# Local Testing Guide

Use this guide to verify `vssctl` without changing your working catalog or generated files. The commands below target Linux/macOS shells; on Windows, use `.venv\Scripts\activate` when activating the virtual environment.

## 1. Create an Isolated Test Copy

Run these commands from the repository root:

```bash
TEST_DIR=$(mktemp -d /tmp/vssctl-manual.XXXXXX)

rsync -a \
  --exclude=.git \
  --exclude=.venv \
  --exclude=.venv_win \
  --exclude=__pycache__ \
  ./ "$TEST_DIR/"

cd "$TEST_DIR"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -e .
```

## 2. Run Basic Checks

```bash
vssctl --help
vssctl doctor
vssctl completion bash
```

Each command should exit successfully. `doctor` currently prints platform information followed by `OK`.

## 3. Test Signal Management

Start the interactive prompt:

```bash
vssctl signal add
```

Enter the following example values:

```text
Node type: signal
Parent: Vehicle.ADAS
Name: ManualTestSpeed
Description: Manual test speed
Datatype: float
Unit: km/h
```

Verify the new signal and catalog:

```bash
vssctl signal search ManualTest
vssctl signal list
vssctl validate
```

Validation should report that the catalog is valid. Test removal with:

```bash
vssctl signal remove Vehicle.ADAS.ManualTestSpeed
vssctl signal search ManualTest
```

The final search should report no matching signals. Add the signal again before testing generation.

## 4. Test VSS Generation

```bash
vssctl generate --version 6.0
```

Confirm the generated sensor metadata:

```bash
jq -e '
  .Vehicle.children.ADAS.children.ManualTestSpeed
  | .type == "sensor"
    and .datatype == "float"
    and .unit == "km/h"
' workspace/generated/json_tree/vss_release_6.0.json
```

The command should print `true`. Install `jq` first if it is unavailable.

## 5. Test the Terminal UI

Run this in an interactive terminal:

```bash
vssctl browse --source custom
```

Confirm that the custom tree opens and `ManualTestSpeed` can be found.

## 6. Run the Automated Suite

```bash
python -m pip install pytest
python -m pytest tests/ -q
```

All tests should pass without changing the repository's catalog or generated output.

## Optional Container Test

A container test requires a running Docker or Podman engine and a KUKSA Databroker checkout under `workspace/databroker/kuksa-databroker`.

```bash
vssctl build \
  --vss-file workspace/generated/json_tree/vss_release_6.0.json \
  --engine docker \
  --databroker-dir workspace/databroker

docker image inspect kuksa-databroker:vss-6.0
docker run --rm -p 55555:55555 kuksa-databroker:vss-6.0
```

Stop the container with `Ctrl+C`. Do not run `vssctl publish` unless you intentionally want to push an image to a registry.
