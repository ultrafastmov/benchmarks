#!/usr/bin/env python3
"""Prints the machine and software the benchmark ran on, as JSON (results/environment.json)."""
import hashlib
import json
import os
import platform
import re
import subprocess

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=120)
        return (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"unavailable: {e}"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pkg_version(project, name):
    try:
        with open(os.path.join(BENCH, project, "node_modules", name, "package.json")) as f:
            return json.load(f)["version"]
    except OSError:
        return None


def main():
    cpu = sh(["lscpu"])
    model = re.search(r"Model name:\s*(.+)", cpu)
    threads = re.search(r"^CPU\(s\):\s*(\d+)", cpu, re.M)
    cores = re.search(r"Core\(s\) per socket:\s*(\d+)", cpu)
    maxmhz = re.search(r"CPU max MHz:\s*([\d.]+)", cpu)
    with open("/proc/meminfo") as f:
        mem_kb = int(re.search(r"MemTotal:\s*(\d+)", f.read()).group(1))
    gpu = sh(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,pcie.link.gen.max,power.limit",
              "--format=csv,noheader"])
    os_release = {}
    with open("/etc/os-release") as f:
        for line in f:
            if "=" in line:
                k, v = line.rstrip().split("=", 1)
                os_release[k] = v.strip('"')
    uf = os.environ.get("UF", "")
    ff_dir = os.path.join(BENCH, "tools", "ffmpeg", "ffmpeg-n9.0.2-61-gd59078794d-linux64-gpl-9.0", "bin")
    rm_shell = os.path.join(BENCH, "remotion", "node_modules", ".remotion", "chrome-headless-shell",
                            "linux64", "chrome-headless-shell-linux64", "chrome-headless-shell")
    hf_cache = os.environ.get("HYPERFRAMES_CACHE_DIR", os.path.join(BENCH, ".cache", "hyperframes"))
    hf_shell = None
    for root, _dirs, files in os.walk(os.path.join(hf_cache, "chrome")):
        if "chrome-headless-shell" in files:
            hf_shell = os.path.join(root, "chrome-headless-shell")
    info = {
        "cpu": {"model": model.group(1).strip() if model else None,
                "cores": int(cores.group(1)) if cores else None,
                "threads": int(threads.group(1)) if threads else None,
                "max_mhz": float(maxmhz.group(1)) if maxmhz else None},
        "ram_gib": round(mem_kb / 2**20, 1),
        "gpu": gpu,
        "os": f"{os_release.get('NAME')} {os_release.get('VERSION_ID')}",
        "kernel": platform.release(),
        "node": sh(["node", "--version"]),
        "npm": sh(["npm", "--version"]),
        "ffmpeg_system": sh(["ffmpeg", "-hide_banner", "-version"]).splitlines()[0],
        "ffmpeg_hyperframes": sh([os.path.join(ff_dir, "ffmpeg"), "-hide_banner", "-version"]).splitlines()[0],
        "ultrafast": {"version": sh([uf, "--version"]) if uf else None,
                      "binary_sha256": sha256(uf) if uf and os.path.exists(uf) else None,
                      "device": sh([uf, "info"]) if uf else None},
        "remotion": {"remotion": pkg_version("remotion", "remotion"),
                     "@remotion/cli": pkg_version("remotion", "@remotion/cli"),
                     "@remotion/media": pkg_version("remotion", "@remotion/media"),
                     "react": pkg_version("remotion", "react"),
                     "chrome_headless_shell": sh([rm_shell, "--version"]) if os.path.exists(rm_shell) else None},
        "hyperframes": {"hyperframes": pkg_version("hyperframes", "hyperframes"),
                        "gsap": pkg_version("hyperframes", "gsap"),
                        "chrome_headless_shell": sh([hf_shell, "--version"]) if hf_shell else None},
    }
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
