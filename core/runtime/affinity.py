# /BrainBot/core/runtime/affinity.py
# BrainBot Affinity Controller
# Created by: David Kistner (Unconditional Love)



#system imports
import psutil
import threading
from contextlib import contextmanager



# ----------------------------------
# List available CPU cores
# ----------------------------------
def list_available_cores():
    """
    Returns a list of available CPU core indices.
    Example: [0, 1, 2, 3, ...]
    """
    try:
        return list(range(psutil.cpu_count()))
    except Exception:
        return []

# ------------------------------------------
# Pin the *current thread* to a single core
# ------------------------------------------
def pin_thread_to_core(core_index: int):
    """
    Pin ONLY the current thread to a specific CPU core.
    This is useful for deterministic LLM execution.

    NOTE:
    - On Linux/Windows, psutil supports affinity.
    - On macOS, this silently does nothing (correct behavior).
    """
    try:
        p = psutil.Process()
        if hasattr(p, "cpu_affinity"):
            p.cpu_affinity([core_index])
            return True
    except Exception:
        pass

    return False

# ----------------
# Set Affinity
# ----------------
@contextmanager
def set_affinity(cores):
    """
    Temporarily set CPU affinity for the *current thread* during LLM inference.
    Falls back gracefully on systems without affinity support.
    """
    try:
        p = psutil.Process()
        old_affinity = p.cpu_affinity() if hasattr(p, "cpu_affinity") else None

        # Apply affinity only if supported
        if hasattr(p, "cpu_affinity") and isinstance(cores, (list, tuple)):
            p.cpu_affinity(cores)

        yield

    finally:
        # Restore previous affinity
        try:
            if hasattr(p, "cpu_affinity") and old_affinity is not None:
                p.cpu_affinity(old_affinity)
        except Exception:
            pass

