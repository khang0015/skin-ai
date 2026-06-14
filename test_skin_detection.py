"""Quick test script to verify skin detection fix."""
import cv2
import numpy as np

# Simulate a skin-colored image (fair skin like the user's photo)
# Fair skin BGR roughly: B=180, G=160, R=200
skin_img = np.full((100, 100, 3), [180, 160, 200], dtype=np.uint8)
# Add some variation
noise = np.random.randint(-15, 15, skin_img.shape, dtype=np.int16)
skin_img = np.clip(skin_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

# Non-skin image (blue sky)
blue_img = np.full((100, 100, 3), [230, 150, 50], dtype=np.uint8)

import sys
sys.path.insert(0, ".")
from backend.app.services.skin_detector import compute_skin_ratio, is_skin_image

print("=== Skin Detection Test ===")
print()

ratio_skin = compute_skin_ratio(skin_img)
is_skin, r = is_skin_image(skin_img)
print(f"Simulated SKIN image:  ratio = {ratio_skin:.2%}, is_skin = {is_skin}")

ratio_blue = compute_skin_ratio(blue_img)
is_blue, r2 = is_skin_image(blue_img)
print(f"Simulated BLUE image:  ratio = {ratio_blue:.2%}, is_skin = {is_blue}")

# Also test with a green image
green_img = np.full((100, 100, 3), [50, 200, 50], dtype=np.uint8)
ratio_green = compute_skin_ratio(green_img)
is_green, r3 = is_skin_image(green_img)
print(f"Simulated GREEN image: ratio = {ratio_green:.2%}, is_skin = {is_green}")

print()
if is_skin and not is_blue and not is_green:
    print("✅ All tests PASSED!")
else:
    print("❌ Some tests FAILED!")
    if not is_skin:
        print("  - Skin image was NOT detected as skin")
    if is_blue:
        print("  - Blue image was wrongly detected as skin")
    if is_green:
        print("  - Green image was wrongly detected as skin")
