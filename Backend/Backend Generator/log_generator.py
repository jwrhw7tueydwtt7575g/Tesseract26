#!/usr/bin/env python3
"""
Synthetic Kubernetes log generator.

Behavior:
- Writes all logs to stdout (Kubernetes-native logging).
- Mixes normal INFO logs with occasional WARN/ERROR bursts.
- Supports MODE via environment variable:
    - random   -> random pillar on each burst (default)
    - health   -> only health-related errors
    - anomaly  -> only anomaly-related warnings
    - service  -> only service-related errors
    - security -> only security-related warnings
"""

import logging
import os
import random
import time
from typing import Dict, List, Literal, Tuple

Mode = Literal["random", "health", "anomaly", "service", "security"]
Pillar = Literal["health", "anomaly", "service", "security"]

VALID_MODES = {"random", "health", "anomaly", "service", "security"}

# Configure logging to stdout.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

NORMAL_INFO_MESSAGES: List[str] = [
    "server started on :8080",
    "GET /api/health 200 OK",
    "GET /api/users 200 OK latency=28ms",
    "POST /api/login 200 OK latency=74ms",
    "worker heartbeat ok queue_depth=3",
    "db connection pool healthy active=7 idle=13",
    "cache refresh completed entries=248",
    "background sync completed in 0.41s",
    "ingress request GET / 200 OK",
    "metrics push successful batch=120",
    "liveness probe passed",
    "readiness probe passed",
]

def _generate_dynamic_normal_log() -> str:
    """Generate normal logs with random but realistic metric values"""
    return random.choice([
        f"GET /api/users 200 OK latency={random.randint(20, 150)}ms",
        f"POST /api/orders 200 OK latency={random.randint(50, 250)}ms",
        f"worker heartbeat ok queue_depth={random.randint(1, 50)}",
        f"Heap memory usage at {random.randint(30, 60)}% - {random.randint(1200, 2000)}MB/4000MB",
        f"CPU usage: {random.randint(10, 50)}% (threshold=80%)",
        f"Database query on postgres: {random.randint(10, 200)}ms",
        f"GET /api/inventory 200 OK - {random.randint(100, 500)}ms",
        f"Garbage collection completed in {random.randint(50, 300)}ms",
        f"Health check: OK - all services healthy - latency={random.randint(5, 50)}ms",
    ])


def _health_error() -> str:
    return random.choice(
        [
            f"OOMKill - container exceeded {random.choice([256, 384, 512, 768, 1024])}Mi",
            f"CrashLoopBackOff - restart count={random.randint(3, 18)} in last {random.choice([1, 5, 10])}m",
            f"Liveness probe failed - HTTP probe statuscode: {random.choice([500, 503, 504])}",
            f"Readiness probe failed - timeout after {random.randint(2, 8)}s",
            f"Container unhealthy - backoff restarting failed container ({random.randint(5, 40)}s)",
        ]
    )


def _anomaly_warning() -> str:
    cpu = random.randint(88, 99)
    latency = random.randint(5000, 15000)
    mem = random.randint(82, 98)
    queue_depth = random.randint(600, 1200)
    gc_time = random.randint(2000, 8000)
    return random.choice(
        [
            f"CPU throttling at {cpu}% - response latency={latency}ms",
            f"WARN: Heap memory critical: {mem}% - {int(mem*40)}MB/4000MB - attempting GC in {gc_time}ms",
            f"CRITICAL: high latency detected p95={latency}ms endpoint=/api/orders timeout=true",
            f"CRITICAL: Request queue depth: {queue_depth} (threshold=500) - service degraded",
            f"ERROR: Connection timeout after {random.randint(45, 120)}s to user-service:5432",
            f"anomaly score={random.uniform(0.80, 0.99):.2f} above threshold=0.75 - latency={latency}ms",
            f"CRITICAL: Garbage collection overhead limit exceeded - GC time={gc_time}ms",
        ]
    )


def _service_error() -> str:
    return random.choice(
        [
            "503 Service Unavailable - no endpoints",
            f"502 Bad Gateway - upstream connect error to svc/payment:{random.choice([8080, 9090])}",
            f"504 Gateway Timeout - upstream request exceeded {random.randint(5, 30)}s",
            f"connection refused while dialing upstream {random.choice(['user-svc', 'order-svc', 'inventory-svc'])}",
            f"upstream reset before headers from {random.choice(['auth-svc', 'billing-svc'])}",
        ]
    )


def _security_warning() -> str:
    ip = f"192.168.{random.randint(0, 10)}.{random.randint(2, 254)}"
    return random.choice(
        [
            f"401 Unauthorized from {ip}",
            f"403 Forbidden for user=system:serviceaccount:default:{random.choice(['viewer', 'agent', 'unknown'])}",
            "RBAC deny: user cannot list secrets in namespace=prod",
            f"permission denied while accessing /admin from {ip}",
            f"multiple failed auth attempts={random.randint(3, 12)} source={ip}",
        ]
    )


PILLAR_GENERATORS: Dict[Pillar, Tuple[str, callable]] = {
    "health": ("ERROR", _health_error),
    "anomaly": ("WARNING", _anomaly_warning),
    "service": ("ERROR", _service_error),
    "security": ("WARNING", _security_warning),
}


def _emit_pillar_log(pillar: Pillar) -> None:
    level, generator = PILLAR_GENERATORS[pillar]
    message = generator()
    if level == "ERROR":
        logger.error(message)
    else:
        logger.warning(message)


def generate_logs(interval: float = 1.5) -> None:
    mode_raw = os.getenv("MODE", "random").strip().lower()
    mode: Mode = mode_raw if mode_raw in VALID_MODES else "random"

    if mode_raw not in VALID_MODES:
        logger.warning(
            "Invalid MODE '%s'. Falling back to MODE=random. Valid values: %s",
            mode_raw,
            ", ".join(sorted(VALID_MODES)),
        )

    logger.info("Log generator started")
    logger.info("MODE=%s", mode)
    logger.info("Emitting mixed normal logs with occasional pillar error bursts")

    try:
        while True:
            # Normal traffic first (1 to 4 INFO lines with REAL METRICS).
            for _ in range(random.randint(1, 4)):
                logger.info(_generate_dynamic_normal_log())
                time.sleep(random.uniform(0.4, 1.8))

            # Error burst chance to mimic real incidents.
            if random.random() < 0.72:
                burst_size = random.randint(1, 4)
                for _ in range(burst_size):
                    if mode == "random":
                        pillar: Pillar = random.choice(
                            ["health", "anomaly", "service", "security"]
                        )
                    else:
                        pillar = mode

                    _emit_pillar_log(pillar)
                    time.sleep(random.uniform(0.2, 1.0))

            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Log generator interrupted by user")
    finally:
        logger.info("Log generator stopped")


if __name__ == "__main__":
    generate_logs()
