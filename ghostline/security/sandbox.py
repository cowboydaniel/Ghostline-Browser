"""Sandbox profiles expressed as allowlists for filesystem and syscalls."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class SandboxProfile:
    name: str
    allowed_syscalls: List[str] = field(default_factory=list)
    allowed_paths: List[str] = field(default_factory=list)

    def ensure_seccomp_minimums(self) -> None:
        required_syscalls = {"read", "write", "exit", "rt_sigreturn"}
        for syscall in required_syscalls:
            if syscall not in self.allowed_syscalls:
                self.allowed_syscalls.append(syscall)

    def allow_profile_storage(self, profile_dir: str) -> None:
        if profile_dir not in self.allowed_paths:
            self.allowed_paths.append(profile_dir)


DEFAULT_CONTENT_PROFILE = SandboxProfile(
    name="content",
    allowed_syscalls=["openat", "close", "fstat", "mmap", "munmap"],
    allowed_paths=["/usr/lib/qt6", "/usr/share/ca-certificates"],
)
DEFAULT_CONTENT_PROFILE.ensure_seccomp_minimums()
