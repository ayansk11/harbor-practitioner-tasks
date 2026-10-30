"""Shared grading helpers for the five tasks (submission/base/verifier_kit; synced into each task's tests/).

Threat model. FACT from the Daytona infra pilot (docs/evidence/local_checks_2026-10-28.txt ADDENDUM 5): the verifier
runs as root in its own container with cwd /tests; /tests is 0700, so uid 1001 cannot read it; Harbor leaves
/logs/verifier at 0777; the verifier can reach the internet. The agent's /app comes back as an artifact, and its code
runs here as uid 1001 ("runner"). What the kit does about it:
- test.sh writes reward 0 first, locks /logs/verifier (root, 0755), proves the lock with a uid-1001 probe, and strips
  setuid/setgid bits. Then it runs `python3 -I /tests/grade.py`; -I keeps the script folder off sys.path, so grade.py
  adds /tests itself.
- Agent code runs only through run_as_runner / start_service_as_runner: a new session, uid and gid 1001, no
  supplementary groups, PR_SET_NO_NEW_PRIVS, rlimits (no core files; file size, open files and process count capped),
  stdin from /dev/null, output to anonymous files (only a 4000-byte tail is kept), and a private network namespace with
  loopback only when the kernel allows it and no service is live. After every run, every leftover uid-1001 process
  outside a live service is killed, setsid() escapes included.
- Root never follows a path that uid 1001 can change. /work is root-owned 1777 (the runner can add entries but cannot
  move root's). Copies are made while no runner process is alive, and ownership is handed over deepest entry first, so
  no path component can be swapped mid-way. Agent outputs are read only through read_as_runner, or copied with
  copy_out_as_runner into kit.SCRATCH (root-only, 0700).
- write_reward kills every uid-1001 process, re-locks the folder, then writes reward.txt and reward.json through temp
  files and rename(2) (the fail-closed 0 is never deleted first). It reads them back to check them, and on any failure
  writes 0.
Known limits: a service started by start_service_as_runner keeps the host network (it can reach the internet); whether
the kernel allows a private network namespace on Daytona is UNVERIFIED (the first run logs it); all real-mode steps
are proven only by the Daytona proof run, not on the Mac.

Local mode (authoring on the Mac only): KIT_LOCAL=1 and not root. Paths come from KIT_SUBMISSION (the agent's /app
copy), KIT_LOGS, KIT_WORK and GRADE_TESTS_DIR. Demotion, chown, the uid-1001 kill loop and the network namespace are
skipped. Local mode can never trigger in the real verifier, which runs as root. Real mode refuses to start unless it
runs as root from /tests/kit.py.
"""
import atexit, json, math, numbers, os, resource, shutil, signal, socket, stat, struct, subprocess, sys, tempfile, time
import traceback

try:
    import fcntl
except ImportError:  # not on Linux or macOS
    fcntl = None

RUNNER_UID = 1001
RUNNER_GID = 1001
LOCAL = os.environ.get("KIT_LOCAL") == "1" and os.getuid() != 0
APP_DIR = os.path.abspath(os.environ.get("KIT_SUBMISSION", "/app")) if LOCAL else "/app"
LOGS = os.path.abspath(os.environ.get("KIT_LOGS", "/tmp/kit-logs")) if LOCAL else "/logs/verifier"
WORK = os.path.abspath(os.environ.get("KIT_WORK", "/tmp/kit-work")) if LOCAL else "/work"
TESTS_DIR = os.path.abspath(os.environ.get("GRADE_TESTS_DIR", "/tests")) if LOCAL else "/tests"
AUTORUN_NAMES = {"conftest.py", "sitecustomize.py", "usercustomize.py"}
AUTORUN_STEMS = {"sitecustomize", "usercustomize"}  # any form: .py, .pyc, package folder, extension module
RUNNER_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp/runner-home", "LANG": "C.UTF-8",
              "LC_ALL": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1"}
if LOCAL:
    RUNNER_ENV["HOME"] = os.path.join(WORK, ".runner-home")
RUNNER_FSIZE_BYTES = 1 << 30   # largest file any runner process may write (RLIMIT_FSIZE); per call: fsize_bytes=
RUNNER_OUTPUT_BYTES = 64 << 20  # stdout + stderr of one run; past it the run is killed (output_capped); per call: output_bytes=
RUNNER_NPROC = 512             # processes plus threads of uid 1001 (RLIMIT_NPROC; real mode only)
RUNNER_NOFILE = 4096           # open files per runner process (RLIMIT_NOFILE; real mode only)
ISOLATE_NETWORK = True         # private network namespace for runs when possible; a grader may set kit.ISOLATE_NETWORK = False
PR_SET_NO_NEW_PRIVS = 38

_SERVICES = {}   # pid (= session id) -> Popen, for services started by start_service_as_runner
_NETNS = None    # None = not probed yet


def log(msg):
    text = f"[kit] {msg}".encode("utf-8", "backslashreplace").decode("utf-8")  # odd file names never crash a log line
    print(text, flush=True)


if not LOCAL:
    _here = os.path.realpath(os.path.abspath(__file__))
    if os.getuid() != 0 or _here != os.path.realpath("/tests/kit.py") or not os.path.isfile("/tests/test.sh"):
        raise SystemExit("[kit] refusing to start: real mode runs only as root in the verifier container, from "
                         "/tests/kit.py. For local authoring run as a normal user with KIT_LOCAL=1.")
    os.umask(0o022)

SCRATCH = tempfile.mkdtemp(prefix="kit-scratch-", dir=None if LOCAL else "/tmp")  # root-only (0700) scratch folder
if LOCAL:
    atexit.register(shutil.rmtree, SCRATCH, True)

_PRCTL = None
if not LOCAL and sys.platform.startswith("linux"):
    try:
        import ctypes
        _PRCTL = ctypes.CDLL(None, use_errno=True).prctl
        _PRCTL.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
        _PRCTL.restype = ctypes.c_int
    except Exception as _e:  # PR_SET_NO_NEW_PRIVS then relies on test.sh's setuid strip
        _PRCTL = None
        log(f"WARNING: prctl not available ({_e!r}); runs go without PR_SET_NO_NEW_PRIVS")


# ---------------------------------------------------------------- child side (runs between fork and exec)

def _child_note(msg):
    try:
        os.write(2, f"[kit-preexec] {msg}\n".encode("utf-8", "replace"))
    except OSError:
        pass


def _child_limits(fsize):
    wanted = [(resource.RLIMIT_CORE, 0), (resource.RLIMIT_FSIZE, fsize)]
    if not LOCAL:
        wanted += [(resource.RLIMIT_NOFILE, RUNNER_NOFILE), (resource.RLIMIT_NPROC, RUNNER_NPROC)]
    for res, val in wanted:
        if val is None:
            continue
        try:
            _soft, hard = resource.getrlimit(res)
            v = val if hard == resource.RLIM_INFINITY else min(val, hard)
            resource.setrlimit(res, (v, v))
        except Exception as e:
            _child_note(f"rlimit {res} not set: {e!r}")


def _loopback_up():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        flags = struct.unpack("16sh22x", fcntl.ioctl(s, 0x8913, struct.pack("16sh22x", b"lo", 0)))[1]  # SIOCGIFFLAGS
        fcntl.ioctl(s, 0x8914, struct.pack("16sh22x", b"lo", flags | 1))                             # SIOCSIFFLAGS, IFF_UP
    finally:
        s.close()


def _enter_private_netns():
    old = os.open("/proc/self/ns/net", os.O_RDONLY)
    try:
        os.unshare(os.CLONE_NEWNET)
        try:
            _loopback_up()
        except Exception:
            os.setns(old, os.CLONE_NEWNET)
            raise
    finally:
        os.close(old)


def _drop_to_runner():
    """Become uid/gid 1001 with no supplementary groups; any failure is fatal (the child never execs)."""
    os.setgroups([])
    os.setgid(RUNNER_GID)
    os.setuid(RUNNER_UID)
    if (os.getuid(), os.geteuid(), os.getgid(), os.getegid()) != (RUNNER_UID, RUNNER_UID, RUNNER_GID, RUNNER_GID):
        raise OSError("kit: demotion to uid 1001 did not take effect")
    try:
        os.setuid(0)
    except PermissionError:
        return
    raise OSError("kit: uid 1001 could switch back to root")


_demote = _drop_to_runner  # old name, kept


def _set_no_new_privs():
    if _PRCTL is None:
        return
    try:
        if _PRCTL(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
            _child_note("PR_SET_NO_NEW_PRIVS failed")
    except Exception as e:
        _child_note(f"PR_SET_NO_NEW_PRIVS failed: {e!r}")


def _make_preexec(fsize, netns=False):
    def preexec():
        _child_limits(fsize)
        if netns:
            try:
                _enter_private_netns()
            except Exception as e:
                _child_note(f"network isolation failed, host network kept: {e!r}")
        if not LOCAL:
            _drop_to_runner()
            _set_no_new_privs()
    return preexec


# ---------------------------------------------------------------- process bookkeeping (grader side)

def _killpg(pid):
    try:
        os.killpg(pid, signal.SIGKILL)
    except OSError:
        pass


def _exited(proc):
    """True once proc has exited; does not reap it, so its pid and process-group id stay reserved."""
    if proc.returncode is not None:
        return True
    try:
        return os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
    except ChildProcessError:
        return True
    except (AttributeError, OSError):
        return proc.poll() is not None


def _wait_no_reap(proc, timeout, stop=None):
    """Wait up to timeout seconds for proc to exit without reaping it. True if it exited, False on timeout or when
    stop() (checked every few ms) returns True."""
    deadline = None if timeout is None else time.monotonic() + timeout
    delay = 0.0005
    while not _exited(proc):
        if (deadline is not None and time.monotonic() >= deadline) or (stop is not None and stop()):
            return False
        time.sleep(delay)
        delay = min(delay * 2, 0.05)
    return True


def _runner_procs():
    """Live (not zombie) uid-1001 processes as [(pid, session id)], from /proc (Linux only)."""
    out = []
    try:
        names = os.listdir("/proc")
    except OSError:
        return out
    for n in names:
        if not n.isdigit():
            continue
        try:
            with open(f"/proc/{n}/status", "rb") as f:
                status = f.read()
            with open(f"/proc/{n}/stat", "rb") as f:
                st = f.read()
        except OSError:
            continue
        uids, state = (), b"?"
        for line in status.splitlines():
            if line.startswith(b"Uid:"):
                uids = tuple(int(x) for x in line.split()[1:3])   # real, effective
            elif line.startswith(b"State:"):
                parts = line.split()
                state = parts[1] if len(parts) > 1 else b"?"
        if RUNNER_UID not in uids or state in (b"Z", b"X"):
            continue
        try:
            sess = int(st[st.rindex(b")") + 2:].split()[3])          # state ppid pgrp session ...
        except (ValueError, IndexError):
            sess = -1
        out.append((int(n), sess))
    return out


def _reap_service(p):
    if p.returncode is None:
        _killpg(p.pid)
    try:
        p.wait(timeout=5)
    except Exception:
        log(f"WARNING: service pid {p.pid} did not exit after SIGKILL")
    _SERVICES.pop(p.pid, None)
    f = getattr(p, "_kit_stderr", None)
    if f is not None:
        try:
            f.close()
        except Exception:
            pass
        p._kit_stderr = None


def _drop_dead_services():
    for p in list(_SERVICES.values()):
        if _exited(p):
            _reap_service(p)


def _kill_strays(rounds=20):
    """Kill every uid-1001 process that is not part of a live service's session. Real mode only."""
    if LOCAL:
        return 0
    _drop_dead_services()
    keep = set(_SERVICES)
    seen = set()
    for _ in range(rounds):
        pids = [pid for pid, sess in _runner_procs() if sess not in keep]
        if not pids:
            return len(seen)
        seen.update(pids)
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        time.sleep(0.02)
    log(f"WARNING: uid-1001 processes outside services still alive after {rounds} rounds")
    return len(seen)


_KILL_ALL_CODE = "import os, signal\ntry:\n    os.kill(-1, signal.SIGKILL)\nexcept OSError:\n    pass\n"


def _kill_all_as_runner():
    """A helper demoted to uid 1001 calls kill(-1, SIGKILL): the kernel signals every uid-1001 process but the helper."""
    try:
        subprocess.run([sys.executable, "-I", "-S", "-c", _KILL_ALL_CODE], cwd="/", env={"PATH": RUNNER_ENV["PATH"]},
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       preexec_fn=_drop_to_runner, timeout=10)
    except Exception as e:
        log(f"kill helper failed: {e!r}")


def kill_runner_processes(rounds=50):
    """Kill every uid-1001 process, services included, looping until none is left. Returns how many were seen."""
    if LOCAL:
        n = len(_SERVICES)
        for p in list(_SERVICES.values()):
            _reap_service(p)
        return n
    seen = set()
    for _ in range(rounds):
        pids = [pid for pid, _sess in _runner_procs()]
        if not pids:
            break
        seen.update(pids)
        _kill_all_as_runner()
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        time.sleep(0.05)
    else:
        log(f"WARNING: uid-1001 processes still alive after {rounds} rounds")
    for p in list(_SERVICES.values()):
        _reap_service(p)
    return len(seen)


# ---------------------------------------------------------------- folders (root side; no runner process may be alive)

def _remove_path(p):
    try:
        st = os.lstat(p)
    except FileNotFoundError:
        return
    if stat.S_ISDIR(st.st_mode):
        shutil.rmtree(p)          # fd-based, never follows a symlink
    else:
        os.unlink(p)              # a file or a symlink itself


def _check_name(name):
    if (not isinstance(name, str) or not name or name in (".", "..") or "/" in name or "\0" in name
            or name.startswith(".runner-home")):
        raise ValueError(f"kit: bad folder name {name!r} (one plain name, e.g. 'sub')")


def _ensure_work():
    if LOCAL:
        os.makedirs(WORK, exist_ok=True)
        return
    try:
        os.mkdir(WORK, 0o755)
    except FileExistsError:
        pass
    fd = os.open(WORK, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fchown(fd, 0, 0)
        os.fchmod(fd, 0o1777)     # sticky: uid 1001 may add entries but cannot move or delete root's
    finally:
        os.close(fd)


def _reset_home():
    """Give uid 1001 a fresh, empty HOME (root-made, then handed over by fd)."""
    h = RUNNER_ENV["HOME"]
    try:
        _remove_path(h)
        os.makedirs(os.path.dirname(h), exist_ok=True)
        os.mkdir(h, 0o700)
        if not LOCAL:
            fd = os.open(h, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fchown(fd, RUNNER_UID, RUNNER_GID)
                os.fchmod(fd, 0o700)
            finally:
                os.close(fd)
    except Exception as e:
        log(f"WARNING: could not reset the runner HOME {h}: {e!r}")


def _check_tree_size(top, max_bytes, max_entries):
    total = entries = 0
    for root, dirs, files in os.walk(top):
        entries += len(dirs) + len(files)
        for n in files:
            try:
                st = os.lstat(os.path.join(root, n))
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                total += st.st_size
        if entries > max_entries or total > max_bytes:
            raise ValueError(f"kit: {top} is too large (limit {max_entries} entries, {max_bytes} bytes)")
    return total, entries


def _special_file_filter(skipped):
    def ignore(src, names):
        bad = []
        for n in names:
            try:
                m = os.lstat(os.path.join(src, n)).st_mode
            except OSError:
                bad.append(n)
                continue
            if not (stat.S_ISDIR(m) or stat.S_ISREG(m) or stat.S_ISLNK(m)):
                bad.append(n)                  # FIFOs, sockets, devices
        skipped.extend(os.path.join(src, n) for n in bad)
        return bad
    return ignore


def _is_autorun(n):
    return (n in AUTORUN_NAMES or n.split(".", 1)[0] in AUTORUN_STEMS or n == "__pycache__"
            or n.endswith(".pth") or n.endswith(".pyc"))


def _strip_autorun(top):
    removed = 0
    for root, dirs, files in os.walk(top, topdown=True):
        for n in list(dirs):
            if _is_autorun(n):
                _remove_path(os.path.join(root, n))
                dirs.remove(n)
                removed += 1
        for n in files:
            if _is_autorun(n):
                _remove_path(os.path.join(root, n))
                removed += 1
    return removed


def _strip_setid(top):
    paths = [top]
    for root, dirs, files in os.walk(top):
        paths.extend(os.path.join(root, n) for n in dirs + files)
    for p in paths:
        st = os.lstat(p)
        if not stat.S_ISLNK(st.st_mode) and st.st_mode & 0o7000:
            os.chmod(p, stat.S_IMODE(st.st_mode) & ~0o7000)


def _hand_over(top):
    """lchown a root-made tree to uid 1001, deepest entries first, so no ancestor is runner-owned while we work."""
    if LOCAL:
        return
    paths = []
    for root, dirs, files in os.walk(top):
        paths.extend(os.path.join(root, n) for n in dirs + files)
    for p in reversed(paths):
        os.lchown(p, RUNNER_UID, RUNNER_GID)
    os.lchown(top, RUNNER_UID, RUNNER_GID)


def prepare_submission(name="sub", *, max_bytes=2 << 30, max_entries=200_000):
    """Copy the agent's /app to a fresh WORK/<name>, strip auto-run files, hand it to uid 1001. Returns the path.

    Kills every uid-1001 process first (services included). Skips FIFOs, sockets and devices, removes conftest.py,
    sitecustomize/usercustomize in any form, *.pth, *.pyc and __pycache__ (links too), and clears setuid, setgid and
    sticky bits. A tree over max_bytes or max_entries raises ValueError, which kit.main scores 0."""
    _check_name(name)
    kill_runner_processes()
    _ensure_work()
    dst = os.path.join(WORK, name)
    _remove_path(dst)
    _check_tree_size(APP_DIR, max_bytes, max_entries)
    skipped = []
    shutil.copytree(APP_DIR, dst, symlinks=True, ignore=_special_file_filter(skipped))
    removed = _strip_autorun(dst)
    _strip_setid(dst)
    _hand_over(dst)
    _reset_home()
    log(f"submission copied to {dst}; removed {removed} auto-run entries; skipped {len(skipped)} special files")
    return dst


def stage_for_runner(src, name):
    """Copy root-held inputs (a folder or one file, e.g. hidden inputs under kit.TESTS_DIR) into a fresh WORK/<name>
    owned by uid 1001, or make it empty when src is None (an output folder). Returns the folder. Never stage answers.

    Kills stray uid-1001 processes first (live services stay up). The copy is made by root and then handed over
    deepest entry first, so it is safe to call at any point in grading."""
    _check_name(name)
    _kill_strays()
    _ensure_work()
    dst = os.path.join(WORK, name)
    _remove_path(dst)
    if src is None:
        os.mkdir(dst, 0o755)
    elif os.path.isdir(src):
        shutil.copytree(src, dst, symlinks=False)
    else:
        os.mkdir(dst, 0o755)
        shutil.copy2(src, os.path.join(dst, os.path.basename(src)))
    _strip_setid(dst)
    _hand_over(dst)
    log(f"staged {src if src is not None else '(empty)'} for uid 1001 at {dst}")
    return dst


# ---------------------------------------------------------------- running agent code

_NETNS_PROBE = r"""
import errno, fcntl, os, socket, struct
os.unshare(os.CLONE_NEWNET)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
flags = struct.unpack("16sh22x", fcntl.ioctl(s, 0x8913, struct.pack("16sh22x", b"lo", 0)))[1]
fcntl.ioctl(s, 0x8914, struct.pack("16sh22x", b"lo", flags | 1))
s.close()
srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
socket.create_connection(srv.getsockname(), timeout=2).close(); srv.close()
try:
    socket.create_connection(("192.0.2.1", 9), timeout=2).close()
    print("NETNS-LEAK")
except OSError as e:
    print("NETNS-OK" if e.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH) else "NETNS-ERR %r" % (e,))
"""


def _netns_available():
    """Probe once (as root, in a throwaway child) whether runs can get a private loopback-only network."""
    global _NETNS
    if _NETNS is None:
        _NETNS = False
        if LOCAL or fcntl is None or not hasattr(os, "unshare") or not hasattr(os, "setns"):
            log("network isolation: not available here; runs keep the host network")
        else:
            try:
                r = subprocess.run([sys.executable, "-I", "-S", "-c", _NETNS_PROBE], stdin=subprocess.DEVNULL,
                                   capture_output=True, timeout=20)
                _NETNS = r.returncode == 0 and r.stdout.strip() == b"NETNS-OK"
                log(f"network isolation: {'ON (private namespace, loopback only)' if _NETNS else 'OFF'}; probe "
                    f"rc={r.returncode} out={r.stdout.strip()[:80]!r} err={r.stderr.strip()[-160:]!r}")
            except Exception as e:
                log(f"network isolation: OFF (probe failed: {e!r})")
    return _NETNS


def _tail(f, n=4000):
    try:
        size = f.seek(0, os.SEEK_END)
        f.seek(max(0, size - n))
        return f.read().decode("utf-8", "replace")
    except Exception:
        return ""


def _fsize(fsize_bytes):
    if fsize_bytes is None:
        return RUNNER_FSIZE_BYTES
    return None if int(fsize_bytes) < 0 else int(fsize_bytes)   # -1: no file-size cap


def run_as_runner(cmd, cwd, timeout, extra_env=None, *, fsize_bytes=None, isolate_network=None, output_bytes=None):
    """Run agent code as uid 1001 in its own session, capped at `timeout` seconds. Returns a dict with rc, timed_out,
    seconds, stdout and stderr (the last 4000 bytes of each), net ("private" or "host") and output_capped (True if
    stdout plus stderr passed output_bytes, default RUNNER_OUTPUT_BYTES, and the run was killed for it).

    The call returns as soon as the main process exits or the cap is hit. Its process group, and in real mode every
    other uid-1001 process outside a live service, is then killed, so nothing it started survives the call. HOME is
    a fresh empty folder for each run while no service is live. Files are capped at fsize_bytes (default
    RUNNER_FSIZE_BYTES; -1 for no cap). isolate_network: None means a private network whenever possible and no
    service is live; False means the host network."""
    env = dict(RUNNER_ENV)
    if extra_env:
        env.update(extra_env)
    _kill_strays()
    if not _SERVICES:
        _reset_home()
    if isolate_network is None:
        isolate_network = ISOLATE_NETWORK and not _SERVICES
    netns = bool(isolate_network) and _netns_available()
    with tempfile.TemporaryFile(dir=SCRATCH) as fo, tempfile.TemporaryFile(dir=SCRATCH) as fe:
        t0 = time.monotonic()
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe,
                                preexec_fn=_make_preexec(_fsize(fsize_bytes), netns), start_new_session=True)
        cap = RUNNER_OUTPUT_BYTES if output_bytes is None else int(output_bytes)
        flood = lambda: os.fstat(fo.fileno()).st_size + os.fstat(fe.fileno()).st_size > cap
        exited = _wait_no_reap(proc, timeout, stop=flood)
        seconds = round(time.monotonic() - t0, 3)
        output_capped = not exited and flood()
        timed_out = not exited and not output_capped
        _killpg(proc.pid)                     # the unreaped leader still reserves the group id
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            log(f"WARNING: pid {proc.pid} still running 10 s after SIGKILL")
        strays = _kill_strays()
        res = {"rc": proc.returncode, "timed_out": timed_out, "seconds": seconds, "stdout": _tail(fo),
               "stderr": _tail(fe), "net": "private" if netns else "host", "output_capped": output_capped}
    log(f"ran {cmd[:4]}... rc={res['rc']} timed_out={timed_out} {seconds}s net={res['net']} strays_killed={strays}"
        + (f" OUTPUT CAPPED at {cap} bytes" if output_capped else ""))
    return res


def _http_answers(port, path, deadline):
    """True if something on 127.0.0.1:port sends back an HTTP status line before the deadline (hard limit)."""
    left = deadline - time.monotonic()
    if left <= 0:
        return False
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=min(1.0, left))
    except OSError:
        return False
    try:
        s.sendall(f"GET {path} HTTP/1.0\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\n\r\n".encode("latin-1"))
        got = b""
        while len(got) < 5:
            left = deadline - time.monotonic()
            if left <= 0:
                return False
            s.settimeout(min(1.0, left))
            chunk = s.recv(5 - len(got))
            if not chunk:
                return False
            got += chunk
        return got == b"HTTP/"
    except OSError:
        return False
    finally:
        s.close()


def start_service_as_runner(cmd, cwd, port, health_path="/", timeout=30, extra_env=None, *, fsize_bytes=None):
    """Start an HTTP service as uid 1001 on 127.0.0.1 and wait (at most `timeout` seconds in total) until it sends an
    HTTP status line for health_path; any status counts. Returns the Popen, or None. Services keep the host network.
    Stop it with stop_service. Stray uid-1001 processes are killed before the start."""
    env = dict(RUNNER_ENV)
    if extra_env:
        env.update(extra_env)
    _kill_strays()
    if not _SERVICES:
        _reset_home()
    err = tempfile.TemporaryFile(dir=SCRATCH)
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=err, preexec_fn=_make_preexec(_fsize(fsize_bytes)), start_new_session=True)
    except BaseException:
        err.close()
        raise
    proc._kit_stderr = err
    _SERVICES[proc.pid] = proc
    t0 = time.monotonic()
    deadline = t0 + timeout
    while True:
        if _exited(proc):
            log(f"service exited early; stderr tail: {_tail(err, 1500)!r}")
            stop_service(proc)
            return None
        if _http_answers(port, health_path, deadline):
            log(f"service on 127.0.0.1:{port} answered after {time.monotonic() - t0:.2f}s")
            return proc
        left = deadline - time.monotonic()
        if left <= 0:
            break
        time.sleep(min(0.2, left))
    log(f"service did not become healthy in {timeout}s; stderr tail: {_tail(err, 1500)!r}")
    stop_service(proc)
    return None


def stop_service(proc):
    """Kill a service's process group, reap it, then kill every uid-1001 process outside the services still live."""
    if proc is None:
        return
    _reap_service(proc)
    _kill_strays()


# ---------------------------------------------------------------- reading what agent code produced

class RunnerReadError(OSError):
    """read_as_runner could not return the whole file (too large, not a regular file, or timed out)."""


_READ_SCRIPT = ('if [ ! -e "$1" ]; then echo "missing or not visible to the runner" >&2; exit 2; fi; '
                'if [ ! -f "$1" ]; then echo "not a regular file" >&2; exit 3; fi; '
                'exec head -c "$2" -- "$1"')


def read_as_runner(path, max_bytes=200_000_000):
    """Read a file the agent's code produced, with uid 1001's rights (a symlink into /tests then fails).
    Raises FileNotFoundError if it is missing or unreadable, RunnerReadError if it is larger than max_bytes, is not a
    regular file (FIFO, device), or takes over 120 s."""
    path = os.path.abspath(path)
    with tempfile.TemporaryFile(dir=SCRATCH) as out, tempfile.TemporaryFile(dir=SCRATCH) as err:
        try:
            p = subprocess.run(["/bin/sh", "-c", _READ_SCRIPT, "sh", path, str(max_bytes + 1)], cwd="/",
                               env=RUNNER_ENV, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                               preexec_fn=_make_preexec(max_bytes + 65536), start_new_session=True, timeout=120)
        except subprocess.TimeoutExpired:
            raise RunnerReadError(f"runner timed out reading {path}") from None
        msg = _tail(err, 300).strip()
        if p.returncode == 2 or (p.returncode != 0 and p.returncode != 3):
            raise FileNotFoundError(f"runner could not read {path}: {msg or 'rc=%s' % p.returncode}")
        if p.returncode == 3:
            raise RunnerReadError(f"runner refused {path}: {msg}")
        size = out.seek(0, os.SEEK_END)
        if size > max_bytes:
            raise RunnerReadError(f"{path} is larger than max_bytes={max_bytes}")
        out.seek(0)
        return out.read()


def copy_out_as_runner(path, dst):
    """Copy an agent-produced file (read through read_as_runner) to dst inside kit.SCRATCH, the root-only folder.
    A relative dst is taken inside SCRATCH; any other place raises ValueError, in local and real mode alike.
    Returns the absolute destination path."""
    data = read_as_runner(path)
    target = os.path.normpath(dst if os.path.isabs(dst) else os.path.join(SCRATCH, dst))
    if target == SCRATCH or os.path.commonpath([target, SCRATCH]) != SCRATCH:
        raise ValueError(f"copy_out_as_runner: dst must be inside kit.SCRATCH ({SCRATCH}), got {dst!r}: root must "
                         "never write into a folder uid 1001 can change")
    os.makedirs(os.path.dirname(target), mode=0o700, exist_ok=True)
    try:
        os.unlink(target)
    except FileNotFoundError:
        pass
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return target


# ---------------------------------------------------------------- the reward

def _number(v):
    """A finite int or float from v (bool, int, float, numpy scalar), else None."""
    if isinstance(v, bool):
        return int(v)
    if not isinstance(v, numbers.Number) and hasattr(v, "item"):
        try:
            v = v.item()
        except Exception:
            return None
        if isinstance(v, bool):
            return int(v)
    if isinstance(v, numbers.Integral):
        return int(v)
    if isinstance(v, numbers.Real):
        f = float(v)
        return f if math.isfinite(f) else None
    return None


def _payload(reward, metrics):
    r = _number(reward)
    value = 0.0 if r is None else min(1.0, max(0.0, float(r)))
    if r is None or value != r:
        log(f"WARNING: reward {reward!r} is not a number in [0, 1]; written as {value}")
    payload = {"reward": value}
    try:
        items = list(dict(metrics or {}).items())
    except Exception:
        log(f"WARNING: metrics {type(metrics).__name__} is not a mapping; ignored")
        items = []
    for k, v in items:
        key = str(k)
        n = _number(v)
        if key == "reward" or n is None:
            log(f"metric {key!r}={v!r} dropped ({'reserved name' if key == 'reward' else 'not a finite number'})")
            continue
        payload[key] = n
    return value, payload


def _open_logs_dir():
    path = os.path.realpath(LOGS) if LOCAL else LOGS
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        os.makedirs(path, exist_ok=True)
        fd = os.open(path, flags)
    except OSError:                       # a symlink or a file sits there; every runner process is dead by now
        aside = f"{path}.moved-{time.time_ns()}"
        os.rename(path, aside)
        log(f"WARNING: {path} was not a folder; moved it to {aside}")
        os.mkdir(path, 0o755)
        fd = os.open(path, flags)
    if not LOCAL:
        os.fchown(fd, 0, 0)
        os.fchmod(fd, 0o755)
    return fd


def _put(fd, name, data):
    """Write data to name inside the folder fd via a temp file and an atomic rename; the old file is never deleted first."""
    tmp = f"{name}.kit-tmp"
    try:
        os.unlink(tmp, dir_fd=fd)
    except FileNotFoundError:
        pass
    f = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=fd)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(f, view):]
        os.fchmod(f, 0o644)
        os.fsync(f)
    finally:
        os.close(f)
    try:
        if stat.S_ISDIR(os.stat(name, dir_fd=fd, follow_symlinks=False).st_mode):
            os.rename(name, f"{name}.moved-{time.time_ns()}", src_dir_fd=fd, dst_dir_fd=fd)
    except FileNotFoundError:
        pass
    os.rename(tmp, name, src_dir_fd=fd, dst_dir_fd=fd)   # POSIX rename(2): atomic replace of the old file


def _get(fd, name):
    f = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
    try:
        return os.read(f, 1 << 20)
    finally:
        os.close(f)


def _write_zero():
    """Last resort: reward 0 in both files."""
    try:
        fd = _open_logs_dir()
        try:
            _put(fd, "reward.txt", b"0.0\n")
            _put(fd, "reward.json", b'{"reward": 0.0}')
        finally:
            os.close(fd)
        log("reward=0.0 (fallback after an error)")
        return
    except BaseException as e:
        log(f"ERROR: fallback reward write failed: {e!r}")
    for name, data in (("reward.txt", b"0\n"), ("reward.json", b'{"reward": 0.0}')):
        try:
            f = os.open(os.path.join(LOGS, name), os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o644)
            try:
                os.write(f, data)
            finally:
                os.close(f)
        except BaseException:
            pass


def _restore_logs_owner(fd):
    """Give /logs/verifier back to the owner test.sh recorded (a Docker bind mount on a Linux host); mode stays 0755."""
    if LOCAL:
        return
    try:
        uid, gid = (int(x) for x in os.environ.get("KIT_LOGS_OWNER", "0:0").split(":"))
    except ValueError:
        return
    if (uid, gid) == (0, 0):
        return
    try:
        if _runner_procs():
            log("logs owner not restored: uid-1001 processes are still alive")
            return
        for name in ("reward.txt", "reward.json"):
            os.chown(name, uid, gid, dir_fd=fd, follow_symlinks=False)
        os.fchown(fd, uid, gid)
        log(f"gave {LOGS} back to its original owner {uid}:{gid} (mode 0755)")
    except Exception as e:
        log(f"WARNING: could not restore the owner of {LOGS}: {e!r}")


def _free_disk_if_low(min_free=256 << 20):
    try:
        if shutil.disk_usage(LOGS if os.path.isdir(LOGS) else "/").free >= min_free:
            return
    except OSError:
        return
    log("disk nearly full: removing the work folder and the runner HOME before writing the reward")
    for p in (WORK, RUNNER_ENV["HOME"]):
        try:
            _remove_path(p)
        except Exception as e:
            log(f"WARNING: could not remove {p}: {e!r}")


def write_reward(reward, metrics=None):
    """Final step: kill every uid-1001 process, re-lock the log folder, write reward.txt and reward.json (root).
    The reward is clamped to [0, 1] (not a finite number: 0); metrics keep finite numbers only, never 'reward'.
    Any failure writes 0. Never raises."""
    try:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)   # finish the write once it has started
    except (ValueError, OSError):
        pass
    killed = "?"
    try:
        killed = kill_runner_processes()
    except BaseException as e:
        log(f"ERROR in the kill loop: {e!r}")
    if not LOCAL:
        _free_disk_if_low()
    try:
        value, payload = _payload(reward, metrics)
        txt = f"{value}\n".encode()
        js = json.dumps(payload, allow_nan=False).encode()
        fd = _open_logs_dir()
        try:
            _put(fd, "reward.txt", txt)
            _put(fd, "reward.json", js)
            if _get(fd, "reward.txt") != txt or _get(fd, "reward.json") != js:
                raise OSError("reward files did not read back as written")
            log(f"reward={value} (killed {killed} runner processes) metrics={payload}")
            _restore_logs_owner(fd)
        finally:
            os.close(fd)
    except BaseException as e:
        log(f"ERROR writing the reward: {type(e).__name__}: {e}")
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        _write_zero()


class _Terminated(BaseException):
    pass


def _on_sigterm(signum, frame):
    raise _Terminated("SIGTERM (the verifier time limit?)")


def main(grade_fn):
    """Run a task's grade_fn() -> (reward, metrics) and always end with write_reward; any error, exit or SIGTERM
    inside grade_fn scores 0 and prints the traceback."""
    try:
        signal.signal(signal.SIGTERM, _on_sigterm)
    except (ValueError, OSError):
        pass
    try:
        reward, metrics = grade_fn()
    except BaseException as e:  # a crash in grading must never leave a stale or agent-written reward
        log(f"grading error: {type(e).__name__}: {e}")
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        reward, metrics = 0.0, {"grader_error": 1}
    try:
        write_reward(reward, metrics)
    except BaseException as e:
        log(f"ERROR: write_reward raised {e!r}")
        _write_zero()
