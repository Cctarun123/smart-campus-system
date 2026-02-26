from __future__ import annotations

from .authz import role_flags


def role_context(request):
    return role_flags(request.user)
