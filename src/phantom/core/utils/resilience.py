"""
cerebro.core.utils.resilience
─────────────────────────────
Circuit breaker + retry decorators para todos os GCP/network calls.
Preenche o utils/__init__.py vazio que estava custando resiliência zero.

Usage:
    from phantom.core.utils.resilience import retry_gcp, CircuitBreaker

    @retry_gcp
    def minha_funcao_gcp():
        ...
"""

import time
import logging
import functools
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger("cerebro.resilience")

# ─── Tenacity (opcional) ────────────────────────────────────────────────────
# Se tenacity estiver disponível, usa ele. Senão, fallback manual.
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log,
    )
    _HAS_TENACITY = True
except ImportError:
    _HAS_TENACITY = False
    logger.warning("tenacity not available — usando retry manual. Add 'tenacity' to flake.nix.")


def retry_gcp(func: Callable = None, *, max_attempts: int = 3, min_wait: float = 2.0, max_wait: float = 10.0):
    """
    Decorator para qualquer GCP call no codebase.
    Substitui os 61 try/except manuais espalhados em core/gcp/.

    @retry_gcp
    def call_vertex(...): ...

    @retry_gcp(max_attempts=5, max_wait=30)
    def call_discovery_engine(...): ...
    """
    def decorator(f):
        if _HAS_TENACITY:
            return retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
                retry=retry_if_exception_type((
                    ConnectionError,
                    TimeoutError,
                    OSError,
                    # Graceful fallback se google.api_core disponível
                    *_gcp_retryable_exceptions(),
                )),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            )(f)
        else:
            # Fallback manual quando tenacity não está no nix shell
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                last_exc = None
                for attempt in range(max_attempts):
                    try:
                        return f(*args, **kwargs)
                    except (ConnectionError, TimeoutError, OSError) as e:
                        last_exc = e
                        wait = min(min_wait * (2 ** attempt), max_wait)
                        logger.warning(
                            f"[retry_gcp] {f.__name__} attempt {attempt+1}/{max_attempts} "
                            f"failed: {type(e).__name__}. Retrying in {wait:.1f}s..."
                        )
                        time.sleep(wait)
                raise last_exc
            return wrapper

    if func is not None:
        # Usado como @retry_gcp sem parênteses
        return decorator(func)
    return decorator


def _gcp_retryable_exceptions() -> tuple:
    """Retorna exceções GCP retryable se google.api_core disponível."""
    try:
        from google.api_core import exceptions as gcp_exc
        return (
            gcp_exc.ResourceExhausted,   # 429 rate limit
            gcp_exc.ServiceUnavailable,  # 503
            gcp_exc.InternalServerError, # 500
            gcp_exc.DeadlineExceeded,    # timeout
        )
    except ImportError:
        return ()


# ─── Circuit Breaker ─────────────────────────────────────────────────────────

class CircuitState(Enum):
    CLOSED    = "CLOSED"     # Normal — calls passam
    OPEN      = "OPEN"       # Falhou demais — bloqueia calls
    HALF_OPEN = "HALF_OPEN"  # Testando recuperação


@dataclass
class CircuitBreaker:
    """
    Circuit breaker leve sem deps externas.

    O pattern que estava COMENTADO em rerank_client.py L86 —
    agora implementado de verdade.

    Usage:
        cb = CircuitBreaker(name="vertex-ai", failure_threshold=5)

        result = cb.call(minha_func_gcp, arg1, arg2)
    """
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # segundos antes de tentar HALF_OPEN

    # Estado interno
    failures: int = field(default=0, init=False)
    last_failure_time: float = field(default=0.0, init=False)
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"[circuit:{self.name}] HALF_OPEN — tentando recovery")
            else:
                remaining = self.recovery_timeout - elapsed
                raise CircuitOpenError(
                    f"Circuit '{self.name}' OPEN. Recovery em {remaining:.1f}s"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"[circuit:{self.name}] Recovery OK → CLOSED")
        self.failures = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self, exc: Exception):
        self.failures += 1
        self.last_failure_time = time.time()
        logger.warning(
            f"[circuit:{self.name}] Failure {self.failures}/{self.failure_threshold}: "
            f"{type(exc).__name__}: {exc}"
        )
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"[circuit:{self.name}] OPEN — threshold atingido. "
                f"Recovery em {self.recovery_timeout}s"
            )

    @property
    def is_healthy(self) -> bool:
        return self.state == CircuitState.CLOSED

    def reset(self):
        """Manual reset para testes ou recovery forçado."""
        self.failures = 0
        self.state = CircuitState.CLOSED
        logger.info(f"[circuit:{self.name}] Reset manual → CLOSED")


class CircuitOpenError(RuntimeError):
    """Raised quando circuit está OPEN e bloqueia a call."""
    pass


# ─── Registry global de circuit breakers ────────────────────────────────────

_CIRCUIT_REGISTRY: dict[str, CircuitBreaker] = {}

def get_circuit(name: str, **kwargs) -> CircuitBreaker:
    """
    Singleton registry — mesmo circuit breaker para o mesmo serviço.

    cb_vertex   = get_circuit("vertex-ai")
    cb_chromadb = get_circuit("chromadb", failure_threshold=3)
    cb_reranker = get_circuit("reranker", recovery_timeout=30)
    """
    if name not in _CIRCUIT_REGISTRY:
        _CIRCUIT_REGISTRY[name] = CircuitBreaker(name=name, **kwargs)
    return _CIRCUIT_REGISTRY[name]


def circuit_status() -> dict:
    """Health check de todos os circuits — usado no /health endpoint."""
    return {
        name: {
            "state": cb.state.value,
            "failures": cb.failures,
            "healthy": cb.is_healthy,
        }
        for name, cb in _CIRCUIT_REGISTRY.items()
    }
