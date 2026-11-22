#!/usr/bin/env python3
"""Runs one command inside the transient cgroup that bench.py starts with
`systemd-run --user --scope`, and measures it:

  wall_s          time from spawn to exit (perf_counter)
  cpu_s           user+system CPU of every process in the cgroup (cpu.stat)
  peak_ram_bytes  highest anon+shmem memory of the cgroup, sampled every 50 ms
                  (what the tool's processes hold; page cache excluded)
  memory_peak     the kernel's cgroup memory.peak (includes page cache)
  host_busy_s     CPU busy time of the whole machine over the run (/proc/stat),
                  so bench.py can tell how much of it was someone else's

Usage: runner.py <result.json> <log file> <cwd> -- cmd args...
Stdlib only.
"""
import json
import os
import subprocess
import sys
import threading
import time


def cgroup_dir():
    with open("/proc/self/cgroup") as f:
        for line in f:
            if line.startswith("0::"):
                return "/sys/fs/cgroup" + line.strip()[3:]
    raise SystemExit("cgroup v2 required")


def read_kv(path):
    out = {}
    with open(path) as f:
        for line in f:
            k, v = line.split()
            out[k] = int(v)
    return out


def host_busy_jiffies():
    with open("/proc/stat") as f:
        parts = f.readline().split()[1:]
    vals = [int(x) for x in parts]
    idle = vals[3] + vals[4]  # idle + iowait
    return sum(vals[:8]) - idle


def main():
    sep = sys.argv.index("--")
    result_path, log_path, cwd = sys.argv[1:sep]
    cmd = sys.argv[sep + 1:]
    cg = cgroup_dir()
    hz = os.sysconf("SC_CLK_TCK")

    peak = {"anon_shmem": 0}
    stop = threading.Event()

    def sample():
        while not stop.is_set():
            try:
                st = read_kv(os.path.join(cg, "memory.stat"))
                v = st.get("anon", 0) + st.get("shmem", 0)
                if v > peak["anon_shmem"]:
                    peak["anon_shmem"] = v
            except OSError:
                pass
            stop.wait(0.05)

    st0 = read_kv(os.path.join(cg, "memory.stat"))
    own = st0.get("anon", 0) + st0.get("shmem", 0)  # this runner's own memory
    cpu0 = read_kv(os.path.join(cg, "cpu.stat"))["usage_usec"]
    busy0 = host_busy_jiffies()
    th = threading.Thread(target=sample, daemon=True)
    th.start()
    with open(log_path, "wb") as log:
        t0 = time.perf_counter()
        wall_start = time.time()
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL)
        rc = proc.wait()
        t1 = time.perf_counter()
        wall_end = time.time()
    stop.set()
    th.join()
    cpu1 = read_kv(os.path.join(cg, "cpu.stat"))["usage_usec"]
    leftovers = []
    with open(os.path.join(cg, "cgroup.procs")) as f:
        for pid in f.read().split():
            if int(pid) == os.getpid():
                continue
            try:
                with open(f"/proc/{pid}/cmdline", "rb") as c:
                    leftovers.append(c.read().replace(b"\0", b" ").decode(errors="replace")[:300])
            except OSError:
                pass
    busy1 = host_busy_jiffies()
    with open(os.path.join(cg, "memory.peak")) as f:
        memory_peak = int(f.read().strip())
    res = {
        "returncode": rc,
        "wall_s": t1 - t0,
        "start_unix": wall_start,
        "end_unix": wall_end,
        "cpu_s": (cpu1 - cpu0) / 1e6,
        "peak_ram_bytes": max(0, peak["anon_shmem"] - own),
        "memory_peak_bytes": memory_peak,
        "host_busy_s": (busy1 - busy0) / hz,
        "cgroup": cg,
        "leftover_processes": leftovers,
    }
    with open(result_path, "w") as f:
        json.dump(res, f)
    sys.exit(0)


if __name__ == "__main__":
    main()
