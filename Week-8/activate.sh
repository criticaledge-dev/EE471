# Source this file from Ubuntu/WSL: source ./activate.sh
WEEK8_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export VIRTUAL_ENV="$WEEK8_ROOT/.venv"
export PATH="$VIRTUAL_ENV/bin:$PATH"
if [ -d "$WEEK8_ROOT/.native/usr/lib/x86_64-linux-gnu" ]; then
  export LD_LIBRARY_PATH="$WEEK8_ROOT/.native/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
export MPLCONFIGDIR="$WEEK8_ROOT/outputs/matplotlib"
