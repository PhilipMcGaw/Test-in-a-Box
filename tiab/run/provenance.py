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

    return {
        "version": read_text(project_root / "VERSION"),
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
            "unknown",
        ),
        "python_version": platform.python_version(),
    }


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

    manifest = {
        "schema_version": 1,
        "run": {
            "run_id": run_id,
            "status": status,
            "start_utc": start_utc,
            "finish_utc": finish_utc,
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
        "instruments": instruments,
    }

    manifest_path = output_dir / f"run_{run_id}_manifest.json"
    summary_path = output_dir / f"run_{run_id}_summary.md"

    write_json_atomic(manifest_path, manifest)

    lines = [
        f"# Test Run {run_id}",
        "",
        "## Run",
        "",
        f"- Status: **{status}**",
        f"- Started (UTC): `{start_utc}`",
        f"- Finished (UTC): `{finish_utc or 'in progress'}`",
        "",
        "## Test in a Box",
        "",
        f"- Version: `{software.get('version', 'unknown')}`",
        f"- Update channel: `{software.get('update_channel', 'unknown')}`",
        f"- Ref: `{software.get('update_ref', 'unknown')}`",
        f"- Commit: `{software.get('commit', 'unknown')}`",
        f"- Updater: `{software.get('updater_version', 'unknown')}`",
        f"- Python: `{software.get('python_version', 'unknown')}`",
        "",
        "## Configuration provenance",
        "",
        f"- Configuration SHA-256: `{config_hash}`",
        f"- DUT mapping SHA-256: `{mapping_hash}`",
        f"- Generated procedure SHA-256: `{procedure_hash}`",
        "",
        "## Instruments",
        "",
    ]

    if instruments:
        for device_id, identity in instruments.items():
            lines.append(f"### {device_id}")
            lines.append("")
            if isinstance(identity, dict):
                for key, value in identity.items():
                    lines.append(f"- {key}: `{value}`")
            else:
                lines.append(f"- Identity: `{identity}`")
            lines.append("")
    else:
        lines.extend(["No instrument identity was available.", ""])

    lines.extend([
        "## Files",
        "",
        f"- Manifest: `{manifest_path.name}`",
        f"- Run metadata: `run_{run_id}_metadata.csv`",
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
