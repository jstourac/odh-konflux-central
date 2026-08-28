"""MLflow tracking URI overrides when rh-ai route is unreachable from Tekton."""

from __future__ import annotations

import os

from suite.its_trigger_params import CLUSTER_SOURCE_EPHC, is_external_cluster_source

# test-run.sh honors FORCE_PORT_FORWARD=true on OpenShift (kubectl port-forward + PF_PID).
_SHELL_PREFIX = "export FORCE_PORT_FORWARD=true"


def _mlflow_tracking_patch_enabled() -> bool:
    source = os.environ.get("CLUSTER_SOURCE", "").strip()
    return source == CLUSTER_SOURCE_EPHC or is_external_cluster_source(source)


def mlflow_ephc_incluster_tracking_shell() -> str:
    """Tell test-run.sh to port-forward instead of using the MLflow CR route."""
    return _SHELL_PREFIX


def prepend_mlflow_ephc_tracking(run_command: str) -> str:
    cmd = (run_command or "").strip()
    if not cmd:
        return cmd
    if not _mlflow_tracking_patch_enabled():
        return cmd
    return f"{_SHELL_PREFIX} && {cmd}"
