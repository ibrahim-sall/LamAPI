import numpy as np
from z_interpolation import get_elevation

"""Here we defined our reference points in local and WGS84 coordinates 
It comes from images that we placed on street view"""
poses = [
    {
        "local": [29.523456169218413, -16.8032858715582, -3.745546205900862],
        "wgs84": [47.371298, 8.5411435, 423.58]
    },
    {
        "local": [8.437905948692272, 47.39317759366658, -2.984379281961243],
        "wgs84": [47.37191374212907, 8.54109663480698, 411.74]
    },
    {
        "local": [14.209544997177384, -14.455533619628929, 0.6761970895122704],
        "wgs84": [47.37134209318172, 8.540975215978614, 415.62]
    }
]

def elevation(poses):
    """Calculates the elevation for each pose in WGS84 coordinates if there is no elevation value.

    Args:
        poses (_type_): Grounding thruth points for dataset

    Returns:
        _type_: poses with elevation values
    """
    for pose in poses:
        x, y, z = pose["wgs84"]
        if z is None:
            pose["wgs84"][2] = get_elevation("/mnt/lamas/data/MNT/2683_1247.las",y, x)
    return poses

def interpolate_to_wgs84(local_point, poses):
    """
    Interpolates a local reference point to WGS84 coordinates using the three points in poses.
    """
    poses = elevation(poses)
    local_coords = np.array([pose["local"] for pose in poses])
    wgs84_coords = np.array([pose["wgs84"] for pose in poses])
    local_mean = local_coords.mean(axis=0)
    wgs84_mean = wgs84_coords.mean(axis=0)

    weights = np.linalg.lstsq(local_coords - local_mean, local_point - local_mean, rcond=None)[0]
    interpolated_wgs84 = wgs84_mean + np.dot(weights, wgs84_coords - wgs84_mean)

    return interpolated_wgs84


if __name__ == "__main__":
    
    INPUT_FILE = "LIN_poses.txt"
    OUTPUT_FILE = "output.txt"
    local_points = []
    column2_values = []
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if not line.strip() or line.startswith("#") or line.startswith("//"):
                continue
            parts = line.split(",")
            column2_values.append(parts[1].strip())
            local_points.append([float(parts[6]), float(parts[7]), float(parts[8])])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write("# Interpolated WGS84 points with column2\n")
        file.write("# Format: column2, latitude, longitude, elevation\n")
        for local_point, column2 in zip(local_points, column2_values):
            wgs84_point = interpolate_to_wgs84(local_point, poses)
            file.write(f"{column2}, {wgs84_point[0]}, {wgs84_point[1]}, {wgs84_point[2]}\n")

    print(f"Converted points with column2 have been saved to {OUTPUT_FILE}")