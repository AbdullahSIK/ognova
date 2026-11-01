
import os
import subprocess
import streamlit as st
import psutil
import pandas as pd

from datetime import datetime
from streamlit_autorefresh import st_autorefresh


def read_gpu():
    """Read NVIDIA GPU information using nvidia-smi."""

    command = [
        "nvidia-smi",
        "--query-gpu=name,utilization.gpu,memory.used,"
        "memory.total,temperature.gpu",
        "--format=csv,noheader,nounits"
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode != 0:
            return None

        parts = [
            item.strip()
            for item in result.stdout.strip().split(",")
        ]

        if len(parts) < 5:
            return None

        return {
            "name": parts[0],
            "usage": float(parts[1]),
            "memory_used": float(parts[2]),
            "memory_total": float(parts[3]),
            "temperature": float(parts[4])
        }

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        ValueError,
        OSError
    ):
        return None


def show_pc_monitor():

    # Automatic refresh every second
    st_autorefresh(
        interval=1000,
        limit=None,
        key="nova_monitor_refresh"
    )

    st.title("◈ PC Monitor")
    st.caption(
        "Real-time system performance monitoring"
    )

    st.success("● LIVE — UPDATING EVERY SECOND")

    st.warning(
        "This page measures the machine running NOVA. "
        "When hosted in the cloud, readings are from the "
        "cloud server, not your personal PC."
    )

    # Initialize graph history
    if "monitor_history" not in st.session_state:

        st.session_state.monitor_history = {
            "CPU": [],
            "RAM": [],
            "GPU": []
        }

    history = st.session_state.monitor_history

    # CPU
    cpu = psutil.cpu_percent(interval=None)

    # RAM
    memory = psutil.virtual_memory()
    ram = memory.percent

    # Disk
    try:

        if os.name == "nt":
            drive = os.environ.get(
                "SystemDrive", "C:"
            ) + "\\"
        else:
            drive = "/"

        disk = psutil.disk_usage(drive)

        disk_percent = disk.percent
        disk_free = disk.free / (1024 ** 3)

    except OSError:

        disk_percent = 0
        disk_free = 0

    # GPU
    gpu = read_gpu()

    # Save graph readings
    history["CPU"].append(cpu)
    history["RAM"].append(ram)

    if gpu:
        history["GPU"].append(gpu["usage"])

    # Keep only latest 60 readings
    for key in history:
        history[key] = history[key][-60:]

    # Last update time
    st.caption(
        f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
    )

    # Metric cards
    st.subheader("SYSTEM PERFORMANCE")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "CPU USAGE",
            f"{cpu:.0f}%"
        )

        st.caption(
            f"{psutil.cpu_count(logical=True)} logical processors"
        )

    with col2:
        st.metric(
            "RAM USAGE",
            f"{ram:.0f}%"
        )

        st.caption(
            f"{memory.used / (1024 ** 3):.1f} / "
            f"{memory.total / (1024 ** 3):.1f} GB used"
        )

    col3, col4 = st.columns(2)

    with col3:

        if gpu:

            st.metric(
                "GPU USAGE",
                f"{gpu['usage']:.0f}%"
            )

            st.caption(gpu["name"])

            st.caption(
                f"VRAM: {gpu['memory_used']:.0f} / "
                f"{gpu['memory_total']:.0f} MB"
            )

            st.caption(
                f"Temperature: {gpu['temperature']:.0f} °C"
            )

        else:

            st.metric("GPU USAGE", "N/A")
            st.caption(
                "NVIDIA monitoring unavailable"
            )

    with col4:

        st.metric(
            "SYSTEM DRIVE",
            f"{disk_percent:.0f}%"
        )

        st.caption(
            f"{disk_free:.1f} GB free"
        )

    st.divider()

    # Live performance graphs
    st.subheader("LIVE PERFORMANCE")

    st.markdown("**CPU HISTORY**")

    if history["CPU"]:

        st.line_chart(
            pd.DataFrame({
                "CPU": history["CPU"]
            }),
            y="CPU",
            height=180
        )

    st.markdown("**RAM HISTORY**")

    if history["RAM"]:

        st.line_chart(
            pd.DataFrame({
                "RAM": history["RAM"]
            }),
            y="RAM",
            height=180
        )

    st.markdown("**GPU HISTORY**")

    if history["GPU"]:

        st.line_chart(
            pd.DataFrame({
                "GPU": history["GPU"]
            }),
            y="GPU",
            height=180
        )

    else:

        st.info(
            "GPU graph unavailable because NVIDIA readings "
            "could not be collected."
        )

    st.divider()

    st.caption(
        "NOVA PC Monitor • Latest 60 readings • "
        "Automatic 1-second refresh"
    )
