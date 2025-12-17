"""Permission UX and policy enforcement primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set


ONE_TIME_PERMISSIONS = {"camera", "microphone", "geolocation"}


@dataclass
class PermissionPrompt:
    scope: str
    duration: str  # session, once, persistent
    data_access: str
    purpose: str


@dataclass
class PermissionGrant:
    permission: str
    origin: str
    prompt: PermissionPrompt
    granted: bool
    one_time: bool = False
    active: bool = True
    last_used: datetime = field(default_factory=datetime.utcnow)

    def mark_used(self, when: Optional[datetime] = None) -> None:
        self.last_used = when or datetime.utcnow()


class PermissionPolicyEngine:
    """Enforces enterprise compliance modes and exports audit data."""

    def __init__(self, compliance_mode: str = "standard") -> None:
        self.compliance_mode = compliance_mode
        self.rules: Dict[str, Dict[str, Set[str]]] = {
            "standard": {"deny": set(), "allow": set()},
            "strict": {"deny": {"nativeMessaging", "fileSystem"}, "allow": set()},
            "compliance": {"deny": {"clipboard", "biometrics"}, "allow": set()},
        }
        self.audit_events: List[Dict[str, str]] = []

    def allow(self, origin: str, permission: str) -> bool:
        rule = self.rules.get(self.compliance_mode, self.rules["standard"])
        allowed = permission not in rule.get("deny", set())
        self.audit_events.append(
            {"origin": origin, "permission": permission, "mode": self.compliance_mode, "allowed": str(allowed)}
        )
        return allowed

    def export_audit(self) -> List[Dict[str, str]]:
        return list(self.audit_events)


class NativeMessagingGuard:
    """Restricts native messaging connectors to signed allowlists."""

    def __init__(self, allowed_connectors: Optional[Set[str]] = None) -> None:
        self.allowed_connectors: Set[str] = allowed_connectors or set()

    def validate(self, connector_id: str, signed_host: bool) -> bool:
        if connector_id not in self.allowed_connectors:
            return False
        return signed_host


class PermissionManager:
    """Handles prompts, revocation, and exposure logging per origin."""

    def __init__(self, policy_engine: PermissionPolicyEngine | None = None, idle_timeout: timedelta | None = None) -> None:
        self.policy_engine = policy_engine or PermissionPolicyEngine()
        self.idle_timeout = idle_timeout or timedelta(minutes=15)
        self.grants: Dict[str, Dict[str, PermissionGrant]] = {}
        self.exposure_log: List[Dict[str, str]] = []

    def request_permission(
        self, origin: str, permission: str, prompt: PermissionPrompt, one_time: bool = False
    ) -> PermissionGrant:
        allowed = self.policy_engine.allow(origin, permission)
        grant = PermissionGrant(
            permission=permission,
            origin=origin,
            prompt=prompt,
            granted=allowed,
            one_time=one_time or permission in ONE_TIME_PERMISSIONS or prompt.duration == "once",
            active=allowed,
        )
        self.grants.setdefault(origin, {})[permission] = grant
        return grant

    def use_permission(self, origin: str, permission: str, when: Optional[datetime] = None) -> bool:
        grant = self.grants.get(origin, {}).get(permission)
        if not grant or not grant.active:
            return False
        grant.mark_used(when)
        self.exposure_log.append(
            {"origin": origin, "permission": permission, "timestamp": grant.last_used.isoformat()}
        )
        return True

    def revoke_unused(self, now: Optional[datetime] = None) -> None:
        now = now or datetime.utcnow()
        for origin, perms in list(self.grants.items()):
            for permission, grant in perms.items():
                if grant.active and now - grant.last_used > self.idle_timeout:
                    grant.active = False
                    self.exposure_log.append({"origin": origin, "permission": permission, "reason": "auto-revoked"})

    def close_tab(self, origin: str) -> None:
        for permission, grant in self.grants.get(origin, {}).items():
            if grant.one_time and permission in ONE_TIME_PERMISSIONS:
                grant.active = False
                self.exposure_log.append({"origin": origin, "permission": permission, "reason": "tab-closed"})

    def active_permissions(self, origin: str) -> List[str]:
        return [perm for perm, grant in self.grants.get(origin, {}).items() if grant.active]


__all__ = [
    "NativeMessagingGuard",
    "PermissionGrant",
    "PermissionManager",
    "PermissionPolicyEngine",
    "PermissionPrompt",
    "ONE_TIME_PERMISSIONS",
]
