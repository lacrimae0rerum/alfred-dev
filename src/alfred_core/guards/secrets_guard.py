"""Write-time secrets policy.

Wraps the already-pure detection in :mod:`alfred_core.secrets` and turns it
into a :class:`Decision`: block a write that would commit a credential, unless
the destination is a legitimate local secret container (a real ``.env``).

The policy is **fail-closed**: if the scan itself raises, we deny rather than
risk letting an unscanned write through.
"""

from ..secrets import (
    describe_secret_label,
    find_secret_label,
    is_secret_storage_path,
)
from .decision import Decision, allow, deny


def evaluate_write(path: str, content: str) -> Decision:
    """Decide whether writing ``content`` to ``path`` is safe.

    Denies when a secret is detected and the destination is not a recognized
    secret-storage path; allows otherwise. Fails closed (deny) on any scan
    error.
    """
    try:
        label = find_secret_label(content)
        if label and not is_secret_storage_path(path):
            return deny(f"detected {describe_secret_label(label)} in {path}")
        return allow()
    except Exception as exc:  # fail-closed: never let an unscanned write pass
        return deny(f"secret scan failed, blocking by precaution: {exc}")
