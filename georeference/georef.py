"""
This module provides functionality to interpolate local reference points to WGS84 coordinates.

It uses a least squares method to interpolate local coordinates to WGS84 latitude and longitude.
"""

import numpy as np

poses = [
    {
        "local": [29.523456169218413, -16.8032858715582, -3.745546205900862],
        "wgs84": [47.371298, 8.5411435]
    },
    {
        "local": [8.437905948692272, 47.39317759366658, -2.984379281961243],
        "wgs84": [47.37191374212907, 8.54109663480698]
    },
    {
        "local": [14.209544997177384, -14.455533619628929, 0.6761970895122704],
        "wgs84": [47.37134209318172, 8.540975215978614]
    }
]

def interpolate_to_wgs84(local_point):
    """
    Interpolates a local reference point to WGS84 coordinates using the three points in poses.
    """
    local_coords = np.array([pose["local"] for pose in poses])
    wgs84_coords = np.array([pose["wgs84"] for pose in poses])
    local_mean = local_coords.mean(axis=0)
    wgs84_mean = wgs84_coords.mean(axis=0)

    weights = np.linalg.lstsq(local_coords - local_mean, local_point - local_mean, rcond=None)[0]
    interpolated_wgs84 = wgs84_mean + np.dot(weights, wgs84_coords - wgs84_mean)

    return interpolated_wgs84

INPUT_FILE = "/home/ibhou/Documents/visualPositionningSystem/LamAPI/georeference/LIN_poses.txt"
OUTPUT_FILE = "/home/ibhou/Documents/visualPositionningSystem/LamAPI/georeference/output.txt"

if __name__ == "__main__":
    local_points = []
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if not line.strip() or line.startswith("#") or line.startswith("//"):
                continue
            parts = line.split(",")
            local_points.append([float(parts[6]), float(parts[7]), float(parts[8])])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write("# Interpolated WGS84 points\n")
        file.write("# Format: latitude, longitude\n")
        for local_point in local_points:
            wgs84_point = interpolate_to_wgs84(local_point)
            file.write(f"{wgs84_point[0]}, {wgs84_point[1]}\n")

    print(f"Converted points have been saved to {OUTPUT_FILE}")