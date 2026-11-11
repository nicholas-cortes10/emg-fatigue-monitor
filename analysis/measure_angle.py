import numpy as np
import matplotlib.pyplot as plt

img = plt.imread("../docs/images/angle_photo.png")
plt.imshow(img)
plt.title("Click: 1) shoulder end of upper arm  2) elbow joint  3) wrist")
pts = plt.ginput(3, timeout=0)
plt.close()

s, e, w = (np.array(p) for p in pts)
v1, v2 = s - e, w - e
cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
print(f"Elbow angle: {np.degrees(np.arccos(cos)):.1f} degrees")