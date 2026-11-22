import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt, welch

fs = 1000

values = np.loadtxt("../data/raw/isometric_hold_01.csv", skiprows=1)
values = values[1:-1]
window = values[3000:61500]
window = window - np.mean(window)
sos = butter(4, [20, 450], btype="bandpass", fs=fs, output="sos")
filtered = sosfiltfilt(sos, window)

nwin = 5 * fs
t, mf, rms, low = [], [], [], []
for start in range(0, len(filtered) - nwin + 1, fs):
    seg = filtered[start:start + nwin]
    raw_seg = window[start:start + nwin]

    f, pxx = welch(seg, fs=fs, nperseg=1024)
    band = (f >= 20) & (f <= 450)
    cum = np.cumsum(pxx[band])
    mf.append(f[band][np.searchsorted(cum, 0.5 * cum[-1])])

    rms.append(np.sqrt(np.mean(seg ** 2)))

    fr, pr = welch(raw_seg, fs=fs, nperseg=1024)
    low.append(100 * pr[fr < 20].sum() / pr.sum())

    t.append((start + nwin / 2) / fs)

fig, axes = plt.subplots(4, 1, figsize=(12, 11))
axes[0].plot(t, mf, "o-")
axes[0].set_ylabel("Median freq (Hz)")
axes[1].plot(t, rms, "o-")
axes[1].set_ylabel("RMS amplitude")
axes[2].plot(t, low, "o-")
axes[2].set_ylabel("% raw power < 20 Hz")
for ax in axes[:3]:
    ax.axvspan(28, 36, color="orange", alpha=0.15)
    ax.set_xlim(0, 58.5)

tt = np.arange(len(filtered)) / fs
m = (tt >= 24) & (tt <= 40)
axes[3].plot(tt[m], filtered[m], linewidth=0.4)
axes[3].set_title("Filtered signal, 24-40 s into the hold")
axes[3].set_xlabel("Time into hold (s)")

plt.tight_layout()
plt.savefig("bump_check.png", dpi=100)
print("saved bump_check.png")