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


def median_freq_trend(sig, win_s, nperseg, step_s=1):
    nwin = int(win_s * fs)
    t, mf = [], []
    for start in range(0, len(sig) - nwin + 1, step_s * fs):
        seg = sig[start:start + nwin]
        f, pxx = welch(seg, fs=fs, nperseg=nperseg)
        band = (f >= 20) & (f <= 450)
        cum = np.cumsum(pxx[band])
        idx = np.searchsorted(cum, 0.5 * cum[-1])
        mf.append(f[band][idx])
        t.append((start + nwin / 2) / fs)
    t, mf = np.array(t), np.array(mf)
    slope, intercept = np.polyfit(t, mf, 1)
    fit_start = slope * t[0] + intercept
    fit_end = slope * t[-1] + intercept
    pct = 100 * (fit_end - fit_start) / fit_start
    return t, mf, slope, pct


configs = [
    (5, 1024),
    (3,1024),
    (10,1024),
    (5,512)
]

plt.figure(figsize=(10, 5))
for win_s, nperseg in configs:
    t, mf, slope, pct = median_freq_trend(filtered, win_s, nperseg)
    label = f"{win_s} s window, nperseg={nperseg}"
    print(f"{label}: slope {slope:.3f} Hz/s, fitted change {pct:.1f}%")
    plt.plot(t, mf, label=label)

plt.xlabel("Time into hold (s)")
plt.ylabel("Median frequency (Hz)")
plt.title("Median frequency trend under different analysis settings")
plt.legend()
plt.savefig("robustness.png", dpi=100)
print("saved robustness.png")