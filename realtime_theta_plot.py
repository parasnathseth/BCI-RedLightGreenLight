import time
import numpy as np
from scipy.signal import welch
import matplotlib.pyplot as plt

from brainflow_stream import BrainFlowBoardSetup
import brainflow


def remove_dc_offset(eeg_data: np.ndarray) -> np.ndarray:
    return eeg_data - np.mean(eeg_data, axis=1, keepdims=True)


def compute_single_band_power(eeg_data: np.ndarray, sfreq: float, band_range, nperseg: int = 256) -> np.ndarray:
    n_channels = eeg_data.shape[0]
    powers = np.zeros(n_channels)
    for ch in range(n_channels):
        seg = min(nperseg, eeg_data.shape[1])
        seg = max(seg, 64)
        freqs, psd = welch(eeg_data[ch], sfreq, nperseg=seg)
        low, high = band_range
        idx = (freqs >= low) & (freqs <= high)
        if np.any(idx):
            powers[ch] = np.trapezoid(psd[idx], freqs[idx])
        else:
            powers[ch] = 0.0
    return powers


def main(serial_port: str = None, window_seconds: int = 2, refresh_hz: float = 5.0):
    band_name = "theta"
    band_range = (4, 8)

    board_id = brainflow.BoardIds.CYTON_BOARD.value
    setup = BrainFlowBoardSetup(board_id=board_id, serial_port=serial_port, name="Cyton")
    setup.setup()

    sfreq = setup.get_sampling_rate()
    if not sfreq:
        print("Failed to get sampling rate; exiting.")
        return

    eeg_chs = getattr(setup, "eeg_channels", []) or []
    if not eeg_chs:
        eeg_chs = list(range(1, 8 + 1))

    plt.ion()
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar([0], [0.0], width=0.6)
    ax.set_xticks([0])
    ax.set_xticklabels([band_name])
    ax.set_ylabel(f"{band_name.capitalize()} Band Power (a.u.)")
    ax.set_title(f"Real-time {band_name.capitalize()} Power (Avg across channels)")
    ax.set_ylim(0, 1)

    samples_needed = max(int(window_seconds * sfreq), 64)
    dt = 1.0 / refresh_hz

    try:
        time.sleep(max(0.5, window_seconds))
        while True:
            data = setup.get_current_board_data(num_samples=samples_needed)
            if data is None or data.size == 0 or data.shape[1] < len(eeg_chs):
                time.sleep(dt)
                continue
            if max(eeg_chs) >= data.shape[0]:
                time.sleep(dt)
                continue

            eeg = data[eeg_chs, :]
            eeg = remove_dc_offset(eeg)
            powers = compute_single_band_power(eeg, sfreq, band_range)
            avg_val = float(np.mean(powers))

            prev_top = ax.get_ylim()[1]
            new_top = max(prev_top * 0.9 + avg_val * 0.2, max(1e-3, avg_val * 1.2))
            ax.set_ylim(0, new_top)

            bars[0].set_height(avg_val)

            fig.canvas.draw()
            fig.canvas.flush_events()
            time.sleep(dt)
    except KeyboardInterrupt:
        pass
    finally:
        setup.stop()
        plt.ioff()
        plt.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Real-time theta band power visualization for OpenBCI Cyton")
    parser.add_argument("--port", type=str, default=None, help="Serial port like \\ \\ .\\COM3 (Windows) or /dev/ttyUSB0 (Linux)")
    parser.add_argument("--window", type=float, default=2.0, help="Window length in seconds for PSD")
    parser.add_argument("--fps", type=float, default=5.0, help="Refresh rate (updates per second)")
    args = parser.parse_args()

    main(serial_port=args.port, window_seconds=int(args.window), refresh_hz=args.fps)
