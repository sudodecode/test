#!/usr/bin/env bash
# Log generators used by the Tenki CI test workflows.

ts() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
log() { echo "$(ts) $*"; }
red() { printf '\033[31m%s\033[0m' "$*"; }
green() { printf '\033[32m%s\033[0m' "$*"; }
yellow() { printf '\033[33m%s\033[0m' "$*"; }
blue() { printf '\033[1;34m%s\033[0m' "$*"; }
dim() { printf '\033[2m%s\033[0m' "$*"; }

# progress <label> [steps] [delay]: a carriage-return progress bar.
progress() {
  local label=$1 total=${2:-40} delay=${3:-0.05} i n
  for ((i = 1; i <= total; i++)); do
    n=$((i * 30 / total))
    printf '\r%s [%-30s] %3d%%' "$label" "$(printf '%*s' "$n" '' | tr ' ' '#')" $((i * 100 / total))
    sleep "$delay"
  done
  printf '\n'
}

# flood [lines]: prints many lines as fast as possible.
flood() {
  awk -v n="${1:-20000}" 'BEGIN {
    for (i = 1; i <= n; i++) {
      printf "\033[36m[flood]\033[0m line %06d checksum=%08x payload=%s\n", i, (i * 2654435761) % 4294967296, substr("abcdefghijklmnopqrstuvwxyz0123456789", (i % 30) + 1, 6)
    }
  }'
}

# slow <seconds> [label]: streams one line per second.
slow() {
  local seconds=${1:-60} label=${2:-work} i
  for ((i = 1; i <= seconds; i++)); do
    log "$(dim "[$label]") tick $i/$seconds rss=$((200 + RANDOM % 300))MiB"
    sleep 1
  done
}

# gotest <package> <count> [fail_index]: go test style output.
gotest() {
  local pkg=$1 count=${2:-20} fail=${3:-0} i ms
  for ((i = 1; i <= count; i++)); do
    ms=$((RANDOM % 900))
    echo "=== RUN   Test${pkg^}Case$i"
    if [ "$i" = "$fail" ]; then
      echo "    ${pkg}_test.go:$((40 + i)): expected status 200, got 503"
      echo "--- $(red FAIL): Test${pkg^}Case$i (0.${ms}s)"
    else
      echo "--- $(green PASS): Test${pkg^}Case$i (0.${ms}s)"
    fi
  done
  if [ "$fail" != 0 ]; then
    echo "$(red FAIL)	example.com/mono/$pkg	$((RANDOM % 9)).$((RANDOM % 999))s"
    return 1
  fi
  echo "ok  	example.com/mono/$pkg	$((RANDOM % 9)).$((RANDOM % 999))s"
}

# longline [chars]: one very long line.
longline() {
  printf 'LONG LINE (%s chars): ' "${1:-4000}"
  head -c "${1:-4000}" /dev/zero | tr '\0' 'x'
  printf ' END\n'
}

# noisy <lines>: mixed stdout and stderr with colors and timestamps.
noisy() {
  local n=${1:-50} i
  for ((i = 1; i <= n; i++)); do
    case $((i % 7)) in
      0) echo "$(ts) $(yellow WARN) cache miss for module $i" >&2 ;;
      3) echo "$(ts) $(red ERROR) transient: retrying request $i (this is expected)" >&2 ;;
      *) echo "$(ts) $(green INFO) processed item $i of $n" ;;
    esac
  done
}
