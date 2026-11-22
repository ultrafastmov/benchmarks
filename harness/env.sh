# Environment shared by setup.sh, run.sh and the harness: keeps every cache and
# download inside this folder, and turns off telemetry and update checks.
# Source it from the benchmark folder.
: "${BENCH:=$PWD}"
export BENCH
export npm_config_update_notifier=false
export npm_config_fund=false
# HyperFrames: its documented opt-outs and cache location
export HYPERFRAMES_NO_TELEMETRY=1
export DO_NOT_TRACK=1
export HYPERFRAMES_NO_UPDATE_CHECK=1
export HYPERFRAMES_SKIP_SKILLS=1
export HYPERFRAMES_CACHE_DIR="$BENCH/.cache/hyperframes"
export HYPERFRAMES_CONFIG_DIR="$BENCH/.cache/hyperframes-config"
export HYPERFRAMES_EXTRACT_CACHE_DIR="$BENCH/.cache/hyperframes-extract"
mkdir -p "$HYPERFRAMES_CACHE_DIR" "$HYPERFRAMES_CONFIG_DIR" "$HYPERFRAMES_EXTRACT_CACHE_DIR"
chmod 700 "$BENCH/.cache" "$HYPERFRAMES_CACHE_DIR" "$HYPERFRAMES_CONFIG_DIR" 2>/dev/null || true
# ultrafast: the release binary to measure (override with UF=/path/to/ultrafast)
if [ -z "${UF:-}" ]; then
  UF=$(command -v ultrafast || true)
fi
export UF
