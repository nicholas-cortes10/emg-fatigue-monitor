import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt, welch

fs = 1000

values = np.loadtxt("../data/raw/isometric_hold_01.csv", skiprows=1)
values = values[1:-1]
window = values[3000:61500]
window = window - np.mean(window)     # remove the DC offset (~8,150)

sos = butter(4, [20, 450], btype="bandpass", fs=fs, output="sos")
filtered = sosfiltfilt(sos, window)

t = np.arange(len(window)) / fs
fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
axes[0].plot(t, window, linewidth=0.4)
axes[0].set_title("Raw (mean removed)")
axes[1].plot(t, filtered, linewidth=0.4)
axes[1].set_title("Bandpass 20-450 Hz")
axes[1].set_xlabel("Time into window (s)")
plt.tight_layout()
plt.savefig("filter_check.png", dpi=100)
print("saved filter_check.png")

f, pxx = welch(filtered, fs=fs, nperseg=1024)

plt.figure(figsize=(10, 4))
plt.semilogy(f, pxx)
plt.axvline(60, color="red", linestyle="--", alpha=0.5)
plt.xlabel("Frequency (Hz)")
plt.ylabel("Power spectral density")
plt.title("Welch PSD of filtered hold window")
plt.savefig("psd_check.png", dpi=100)
print("saved psd_check.png")
win_s, step_s = 5, 1
nwin = win_s * fs
mf_t, mf_v = [], []

for start in range(0, len(filtered) - nwin + 1, step_s * fs):
    seg = filtered[start:start + nwin]
    f, pxx = welch(seg, fs=fs, nperseg=1024)
    band = (f >= 20) & (f <= 450)
    cum = np.cumsum(pxx[band])
    idx = np.searchsorted(cum, 0.5 * cum[-1])
    mf_v.append(f[band][idx])
    mf_t.append((start + nwin / 2) / fs)

slope, intercept = np.polyfit(mf_t, mf_v, 1)
print(f"median frequency slope: {slope:.3f} Hz/s")

plt.figure(figsize=(10, 4))
plt.plot(mf_t, mf_v, "o-")
plt.plot(mf_t, slope * np.array(mf_t) + intercept, "r--")
plt.xlabel("Time into hold (s)")
plt.ylabel("Median frequency (Hz)")
plt.savefig("mf_trend.png", dpi=100)