import numpy as np
import matplotlib
matplotlib.use("Agg")          # draw to a file, no pop-up window
import matplotlib.pyplot as plt

values = np.loadtxt("../data/raw/isometric_hold_01.csv", skiprows=1)
print("first 3:", values[:3], " last 3:", values[-3:])

values = values[1:-1]          # drop possibly truncated first/last samples
t = np.arange(len(values)) / 1000

fig, axes = plt.subplots(1, 2, figsize=(14, 4))
axes[0].plot(t[:5000], values[:5000], linewidth=0.5)
axes[0].set_title("First 5 s (pickup transient)")
axes[1].plot(t[55000:70000], values[55000:70000], linewidth=0.5)
axes[1].set_title("55-70 s (release)")
for ax in axes:
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("ADC value")
plt.tight_layout()
plt.savefig("window_check.png", dpi=100)
print("saved window_check.png")