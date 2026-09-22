"""Rate limiting configuration.

Uses slowapi (a FastAPI-friendly wrapper around `limits`). The limiter is
keyed on the client's remote address by default.

Default limits apply to all rate-limited endpoints. Sensitive endpoints
(like /login) apply a stricter limit by decorating the route.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
