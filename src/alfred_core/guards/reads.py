"""Sensitive-file-read policy.

Pure port of the detectors from alfred-dev's ``hooks/sensitive-read-guard.py``
(``_is_env_file`` and friends, plus the base-name and full-path registries).
The hook ``main()`` is intentionally NOT ported.

Note on semantics: the upstream hook was *informative* (warn, never block).
T2.3 promotes the same detection to a blocking policy -- ``evaluate_read``
denies a read of a sensitive file and allows everything else.
"""

import os
from typing import Optional

from .decision import Decision, allow, deny


def _is_env_file(base_name: str, _ext: str) -> bool:
    return base_name == ".env" or base_name.startswith(".env.")


def _is_private_key(_base_name: str, ext: str) -> bool:
    return ext in (".pem", ".key", ".p12", ".pfx")


def _is_ssh_private_key(base_name: str, _ext: str) -> bool:
    return base_name in ("id_rsa", "id_ed25519", "id_ecdsa", "id_dsa")


def _is_service_credentials_file(base_name: str, ext: str) -> bool:
    lowered = base_name.lower()

    if lowered in {
        "credentials.json",
        "service-account.json",
        "gcloud-credentials.json",
        ".npmrc",
        ".pypirc",
        "terraform.tfstate",
    }:
        return True

    if ext != ".json":
        return False

    return (
        lowered.startswith("service-account")
        or lowered.startswith("firebase-adminsdk")
        or lowered.endswith("-service-account.json")
    )


def _is_htpasswd(base_name: str, _ext: str) -> bool:
    return base_name == ".htpasswd"


def _is_java_keystore(_base_name: str, ext: str) -> bool:
    return ext in (".jks", ".keystore")


# Detectors evaluated over the file base name: (predicate, description).
_SENSITIVE_PATTERNS = [
    (_is_env_file, "Environment variable file"),
    (_is_private_key, "Private key or certificate"),
    (_is_ssh_private_key, "SSH private key"),
    (_is_service_credentials_file, "Service credentials"),
    (_is_htpasswd, "Apache password file"),
    # AWS credentials are matched by path below: "credentials"/"config" are too
    # generic to match on base name alone.
    (_is_java_keystore, "Java keystore"),
]

# Detectors evaluated over the full (normalized) path.
_PATH_PATTERNS = [
    (".aws/credentials", "AWS credentials"),
    (".aws/config", "AWS config with possible credentials"),
    ("/.docker/config.json", "Docker credentials"),
    ("/.kube/config", "Kubernetes config"),
    ("/.terraform/terraform.tfstate", "Terraform state with possible secrets"),
    (".ssh/", "SSH directory (possible private keys)"),
    (".gnupg/", "GPG directory (possible private keys)"),
]


def _find_sensitive_description(path: str) -> Optional[str]:
    """Return a description if ``path`` points at a sensitive file, else None."""
    normalized_path = path.replace("\\", "/")
    base_name = os.path.basename(normalized_path)
    _, ext = os.path.splitext(base_name)

    for check_fn, description in _SENSITIVE_PATTERNS:
        if check_fn(base_name, ext):
            return description

    for pattern, description in _PATH_PATTERNS:
        if pattern in normalized_path:
            return description

    return None


def evaluate_read(path: str) -> Decision:
    """Deny reading a recognized sensitive file; allow otherwise.

    Fails closed (deny) on any unexpected error during matching.
    """
    if not path:
        return allow()
    try:
        description = _find_sensitive_description(path)
        if description:
            return deny(f"sensitive file: {description} ({path})")
        return allow()
    except Exception as exc:  # fail-closed: deny if matching blows up
        return deny(f"sensitive-read check failed, blocking by precaution: {exc}")
