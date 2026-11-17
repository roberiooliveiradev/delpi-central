"""Fail-closed Linux POSIX ACL review for HML snapshot *candidate* FDs.

Mode, uid and gid are insufficient: an extended ACL may grant an additional
identity access even though the mode appears restrictive. Read only opened
file descriptors, never user-provided pathnames. This helper NEVER attests
snapshot origin, integrity, producer identity or an operational supervisor.

No filesystem mutation, elevated privileges, subprocess, Docker, socket,
network call or MCP entrypoint is present. False means reject or unverifiable.
"""
from __future__ import annotations

import errno
import os

_ACCESS_ACL = "system.posix_acl_access"
_DEFAULT_ACL = "system.posix_acl_default"


def has_no_extended_posix_acl(fd: int, *, directory: bool) -> bool:
    """Allow only verifiably absent POSIX ACL xattrs on the opened inode.

    A successfully read ACL, including a zero-length or mode-equivalent ACL,
    is a denial. Only Linux ENODATA means "this attribute does not exist".
    EACCES, ENOTSUP, EOPNOTSUPP, ENOSYS, missing getxattr and all unexpected
    errors are unverifiable and rejected. Caller must recheck when useful
    after I/O to reduce (not eliminate) privileged TOCTOU opportunities.
    """
    if (
        type(fd) is not int or fd < 0 or type(directory) is not bool
        or not hasattr(os, "getxattr")
    ):
        return False

    names = (_ACCESS_ACL, _DEFAULT_ACL) if directory else (_ACCESS_ACL,)
    for name in names:
        try:
            os.getxattr(fd, name)
        except OSError as exc:
            if exc.errno == errno.ENODATA:
                continue
            return False
        except (TypeError, ValueError, OverflowError):
            return False
        # The presence of an ACL is not permission to promote this candidate.
        return False
    return True
