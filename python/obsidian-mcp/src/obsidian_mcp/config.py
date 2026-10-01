"""
Resolve vaults from the machine-local danfault config (same file `danfault vault` reads):

    ~/.config/danfault/vault.yaml   (or $XDG_CONFIG_HOME/danfault/vault.yaml)

    default_vault: main
    vaults:
      main:
        path: ~/path/to/vault
        db: ~/path/to/main.db   # optional; default: <this project>/data/<name>.db
"""
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class Vault:
    name: str
    path: Path
    db: Path
    is_default: bool


def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "danfault" / "vault.yaml"


def _load() -> dict:
    path = config_path()
    if not path.exists():
        raise ValueError(f"Config not found: {path}. Register a vault with `danfault vault init`.")
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Malformed config (expected a mapping): {path}")
    return data


def _vault(name: str, entry: dict, default: str | None) -> Vault:
    if not entry.get("path"):
        raise ValueError(f"Vault '{name}' has no 'path' in {config_path()}")
    db = entry.get("db")
    return Vault(
        name=name,
        path=Path(os.path.expanduser(entry["path"])),
        db=Path(os.path.expanduser(db)) if db else DATA_DIR / f"{name}.db",
        is_default=name == default,
    )


def list_vaults() -> list[Vault]:
    cfg = _load()
    default = cfg.get("default_vault")
    return [_vault(n, e or {}, default) for n, e in (cfg.get("vaults") or {}).items()]


def resolve(name: str | None = None) -> Vault:
    """Return the named vault, or `default_vault` when no name is given."""
    cfg = _load()
    vaults = cfg.get("vaults") or {}
    default = cfg.get("default_vault")
    name = name or default
    if not name:
        raise ValueError("No vault given and no default_vault in config.")
    if name not in vaults:
        raise ValueError(f"Unknown vault '{name}'. Known: {', '.join(vaults) or '(none)'}")
    return _vault(name, vaults[name] or {}, default)


def vault_for_file(file_path: str) -> Vault | None:
    """Return the registered vault that contains ``file_path``, or None if no vault does."""
    target = Path(os.path.expanduser(file_path)).resolve()
    for v in list_vaults():
        if target.is_relative_to(v.path.resolve()):
            return v
    return None
