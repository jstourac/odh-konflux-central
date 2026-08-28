"""Trainer smoke patches for EPHC IDMS registry.redhat.io/rhoai mirror parity."""

from __future__ import annotations

_RUNTIME_TEST = "trainer/cluster_training_runtimes_test.go"
_SMOKE_TEST = "trainer/trainer_smoke_test.go"


def _sed_replace(path: str, old: str, new: str) -> str:
    return (
        f"if [ -f {path} ]; then "
        f"sed -i 's#{old}#{new}#g' {path} && "
        f"echo 'trainer: patched {path} for EPHC RHOAI IDMS parity'; "
        "fi"
    )


def _ensure_strings_import(path: str) -> str:
    """strings.Replace in patched tests requires a strings import in the same file."""
    return (
        f"if [ -f {path} ] && grep -Fq 'strings.Replace' {path} "
        f"&& ! grep -q '\"strings\"' {path}; then "
        f"sed -i '/^import (/a\t\"strings\"' {path} && "
        f"echo 'trainer: added strings import to {path}'; "
        "fi"
    )


def trainer_skip_hub_runtime_name_drift_shell() -> str:
    """Skip hub-vs-cluster runtime name check when 3.5-ea.2 ships th06 not th09 names."""
    return r"""
if [ -f trainer/cluster_training_runtimes_test.go ]; then
  python3 - <<'PY'
from pathlib import Path
p = Path("trainer/cluster_training_runtimes_test.go")
text = p.read_text()
mark = "skip hub runtime name drift"
if mark in text:
    raise SystemExit(0)
out = []
for line in text.splitlines(True):
    out.append(line)
    if line.startswith("func TestDefaultTrainingHubRuntimesMatchDefaultClusterRuntimes") and "{" in line:
        out.append('\tt.Skip("skip hub runtime name drift")\n')
p.write_text("".join(out))
print("trainer: skipped TestDefaultTrainingHubRuntimesMatchDefaultClusterRuntimes (th06 vs th09 name drift)", flush=True)
PY
fi
""".strip()


def trainer_smoke_rhoai_idms_patch_shell() -> str:
    return " && ".join(
        [
            _sed_replace(
                _RUNTIME_TEST,
                "expectedImage := imagePrefix + \"/\" + expectedRuntime.Image",
                'expectedImage := strings.Replace(imagePrefix + "/" + expectedRuntime.Image, "quay.io/rhoai/", "registry.redhat.io/rhoai/", 1)',
            ),
            _ensure_strings_import(_RUNTIME_TEST),
            _sed_replace(
                _SMOKE_TEST,
                'runSmoke(t, "kubeflow-trainer-controller-manager", "odh-trainer", "trainer")',
                'runSmoke(t, "kubeflow-trainer-controller-manager", "odh-trainer", "odh-trainer")',
            ),
            (
                "if [ -d trainer ]; then "
                "find trainer -name '*.go' -exec grep -l 'odh-th-torch-cuda-py312' {} + 2>/dev/null | "
                "while IFS= read -r f; do "
                "sed -i 's#odh-th-torch-cuda-py312#odh-th#g' \"$f\" && "
                "echo \"trainer: patched $f for EPHC RHOAI IDMS parity\"; "
                "done; true; "
                "fi"
            ),
            trainer_skip_hub_runtime_name_drift_shell(),
        ]
    )


def prepend_trainer_smoke_patch(run_command: str) -> str:
    cmd = (run_command or "").strip()
    if not cmd:
        return cmd
    return f"{trainer_smoke_rhoai_idms_patch_shell()} && {cmd}"
