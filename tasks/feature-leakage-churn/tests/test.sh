#!/bin/bash
# Shared verifier entrypoint (submission/base/verifier_kit; copied into every task's tests/, kept identical by
# tools/sync_kit.py). Runs as root. Fails closed: the reward stays 0 unless grade.py replaces it at the very end.
set -u
umask 022
V=/logs/verifier
mkdir -p "$V"
# 1. The floor: reward 0 before anything else. kit.write_reward later replaces it atomically and never deletes it.
rm -f "$V/reward.json"
echo 0 > "$V/reward.txt"
# 2. Lock the folder before any agent code runs as uid 1001 (Harbor leaves it 0777). If the lock fails, stop at 0.
LOGS_OWNER=$(stat -c '%u:%g' "$V" 2>/dev/null || echo 0:0)
chown root:root "$V" || { echo "[test.sh] LOCK FAILED: chown $V"; exit 0; }
chmod 0755 "$V" || { echo "[test.sh] LOCK FAILED: chmod $V"; exit 0; }
# /logs must not be writable by uid 1001 either, or a runner could swap the whole folder (best effort).
if [ "$(stat -c %u /logs 2>/dev/null)" = 1001 ]; then chown root /logs || echo "[test.sh] WARNING: chown /logs failed"; fi
if [ -n "$(find /logs -maxdepth 0 -perm /022 2>/dev/null)" ]; then
  chmod go-w /logs || echo "[test.sh] WARNING: chmod go-w /logs failed"
fi
# 3. Prove the lock: a process demoted to uid 1001 must fail to create a file there.
PROBE=$(python3 -I -S -c '
import os
os.setgroups([]); os.setgid(1001); os.setuid(1001)
try:
    os.close(os.open("/logs/verifier/.kit-lock-probe", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644))
    print("WROTE")
except PermissionError:
    print("DENIED")
' 2>&1)
rm -f "$V/.kit-lock-probe"
case "$PROBE" in
  *WROTE*) echo "[test.sh] LOCK FAILED: uid 1001 could write to $V"; exit 0 ;;
  *DENIED*) ;;
  *) echo "[test.sh] LOCK FAILED: uid 1001 probe gave no verdict: $PROBE"; exit 0 ;;
esac
# 4. No setuid or setgid programs for uid 1001 to abuse (kit.py also sets PR_SET_NO_NEW_PRIVS on every run).
find / -xdev -type f -perm /6000 -exec chmod a-s {} + 2>/dev/null
echo "[test.sh] lock ok: $V $(stat -c '%u:%g %a' "$V"), /logs $(stat -c '%u:%g %a' /logs), owner before $LOGS_OWNER;" \
     "protected_symlinks=$(cat /proc/sys/fs/protected_symlinks 2>/dev/null || echo '?')" \
     "protected_hardlinks=$(cat /proc/sys/fs/protected_hardlinks 2>/dev/null || echo '?')" \
     "protected_regular=$(cat /proc/sys/fs/protected_regular 2>/dev/null || echo '?');" \
     "setid files left: $(find / -xdev -type f -perm /6000 2>/dev/null | wc -l)"
cd /tests || exit 0
KIT_LOGS_OWNER="$LOGS_OWNER" python3 -I /tests/grade.py
exit 0
