"""Software/configuration provenance for Test in a Box runs."""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(payload: str) -> str:
    return sha256_bytes(payload.encode("utf-8"))


def canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_json(payload: Any) -> str:
    return sha256_text(canonical_json(payload))


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

    return value if isinstance(value, dict) else {}


def read_text(path: Path, default: str = "unknown") -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return default
    return value or default


def collect_software_identity(project_root: Path) -> dict[str, Any]:
    """Return the installed Test in a Box and updater identity."""
    project_root = project_root.resolve()
    update_state = load_json(project_root / ".update-state.json")
    build_info = load_json(project_root / "support" / "BUILD.json")

    return {
        "version": read_text(project_root / "VERSION"),
        "release_stage": build_info.get("release_stage", "unknown"),
        "repository_layout": build_info.get(
            "repository_layout",
            "unknown",
        ),
        "bootstrap_version": build_info.get(
            "bootstrap_version",
            "unknown",
        ),
        "update_channel": update_state.get("channel", "unmanaged"),
        "update_ref": update_state.get("ref", "unknown"),
        "commit": update_state.get("commit", "unknown"),
        "archive_sha256": update_state.get(
            "archive_sha256",
            "unknown",
        ),
        "updated_at": update_state.get("updated_at", "unknown"),
        "updater_version": update_state.get(
            "updater_version",
            build_info.get("updater_version", "unknown"),
        ),
        "python_version": platform.python_version(),
    }


def duration_seconds(
    start_utc: str,
    finish_utc: str | None,
) -> float | None:
    """Return elapsed seconds for ISO-8601 timestamps."""
    if not finish_utc:
        return None

    try:
        start = datetime.fromisoformat(start_utc)
        finish = datetime.fromisoformat(finish_utc)
    except ValueError:
        return None

    return max(0.0, (finish - start).total_seconds())


def configured_instruments(
    configuration: dict[str, Any],
    identities: dict[str, Any],
) -> list[dict[str, Any]]:
    """Describe every configured device, including unused instruments."""
    result: list[dict[str, Any]] = []

    for entry in configuration.get("devices", []):
        device_id = str(entry.get("device_id", "unknown"))
        identity = identities.get(device_id)

        result.append({
            "device_id": device_id,
            "device_type": entry.get("device_type", "unknown"),
            "connection": entry.get("kwargs", {}),
            "channel_labels": entry.get("channel_labels", {}),
            "identity": identity,
            "identity_captured": identity is not None,
        })

    return result


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_run_reports(
    *,
    output_dir: Path,
    run_id: str,
    start_utc: str,
    finish_utc: str | None,
    status: str,
    software: dict[str, Any],
    configuration: dict[str, Any],
    mapping: dict[str, Any],
    generated_code: str,
    instruments: dict[str, Any],
) -> dict[str, Path]:
    """
    Write a machine-readable manifest and human-readable Markdown summary.
    """
    config_hash = sha256_json(configuration)
    mapping_hash = sha256_json(mapping)
    procedure_hash = sha256_text(generated_code)
    elapsed_seconds = duration_seconds(start_utc, finish_utc)
    configured = configured_instruments(configuration, instruments)

    manifest = {
        "schema_version": 1,
        "run": {
            "run_id": run_id,
            "status": status,
            "start_utc": start_utc,
            "finish_utc": finish_utc,
            "duration_seconds": elapsed_seconds,
        },
        "test_in_a_box": software,
        "configuration": {
            "sha256": config_hash,
            "snapshot": configuration,
        },
        "dut_mapping": {
            "sha256": mapping_hash,
            "snapshot": mapping,
        },
        "procedure": {
            "format": "generated_python",
            "sha256": procedure_hash,
            "source": generated_code,
        },
        "configured_instruments": configured,
        "instrument_identities": instruments,
    }

    manifest_path = output_dir / f"run_{run_id}_manifest.json"
    summary_path = output_dir / f"run_{run_id}_summary.md"

    write_json_atomic(manifest_path, manifest)

    duration_text = (
        f"{elapsed_seconds:.3f} seconds"
        if elapsed_seconds is not None
        else "in progress"
    )

    lines = [
        f"# Test in a Box Run Summary — {run_id}",
        "",
        "## Run",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Run ID | `{run_id}` |",
        f"| Status | **{status}** |",
        f"| Started (UTC) | `{start_utc}` |",
        f"| Finished (UTC) | `{finish_utc or 'in progress'}` |",
        f"| Duration | `{duration_text}` |",
        "",
        "## Software",
        "",
        "| Component | Value |",
        "|---|---|",
        f"| Test in a Box | `{software.get('version', 'unknown')}` |",
        f"| Release stage | `{software.get('release_stage', 'unknown')}` |",
        f"| Repository layout | `{software.get('repository_layout', 'unknown')}` |",
        f"| Bootstrap | `{software.get('bootstrap_version', 'unknown')}` |",
        f"| Updater | `{software.get('updater_version', 'unknown')}` |",
        f"| Python | `{software.get('python_version', 'unknown')}` |",
        f"| Update channel | `{software.get('update_channel', 'unknown')}` |",
        f"| Update ref | `{software.get('update_ref', 'unknown')}` |",
        f"| Commit | `{software.get('commit', 'unknown')}` |",
        "",
        "## Configuration provenance",
        "",
        "| Input | SHA-256 |",
        "|---|---|",
        f"| Configuration | `{config_hash}` |",
        f"| DUT mapping | `{mapping_hash}` |",
        f"| Generated procedure | `{procedure_hash}` |",
        "",
        "## Configured instruments",
        "",
    ]

    if configured:
        for instrument in configured:
            device_id = instrument["device_id"]
            device_type = instrument["device_type"]
            lines.extend([
                f"### {device_id}",
                "",
                f"- Device type: `{device_type}`",
                (
                    "- Identity captured: `yes`"
                    if instrument["identity_captured"]
                    else "- Identity captured: `no`"
                ),
            ])

            identity = instrument.get("identity")
            if isinstance(identity, dict):
                for key, value in identity.items():
                    lines.append(f"- {key}: `{value}`")

            labels = instrument.get("channel_labels") or {}
            if labels:
                lines.append("- Channel labels:")
                for position_id, label in sorted(labels.items()):
                    lines.append(f"  - `{position_id}`: {label}")

            lines.append("")
    else:
        lines.extend([
            "No instruments were configured for this run.",
            "",
        ])

    if configured and not instruments:
        lines.extend([
            "> Instrument identities were not captured. This can be expected "
            "when the procedure does not communicate with an instrument or "
            "when a driver does not expose identity information.",
            "",
        ])

    lines.extend([
        "## Files",
        "",
        "| File | Name |",
        "|---|---|",
        f"| Manifest | `{manifest_path.name}` |",
        f"| Run metadata | `run_{run_id}_metadata.csv` |",
        "",
    ])

    summary_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return {
        "manifest": manifest_path,
        "summary": summary_path,
    }
