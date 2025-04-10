import numpy as np
from .z_interpolation import get_elevation

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


def get_weights(local_point, poses = poses):
    """Calculates the weights for each pose based on the local coordinates and WGS84 correspondance.

    Args:
        poses (dic): Grounding thruth points for dataset
        
    Returns:
        list: Weights for each pose.
    """
    poses = elevation()
    local_coords = np.array([pose["local"] for pose in poses])
    local_mean = local_coords.mean(axis=0)

    return np.linalg.lstsq(local_coords - local_mean, local_point - local_mean, rcond=None)[0]

def elevation(poses = poses):
    """Calculates the elevation for each pose in WGS84 coordinates if there is no elevation value.

    Args:
        poses (dic): Grounding thruth points for dataset

    Returns:
        poses (dic): poses with elevation values
    """
    for pose in poses:
        x, y, z = pose["wgs84"]
        if z is None:
            pose["wgs84"][2] = get_elevation("/mnt/lamas/data/MNT/2683_1247.las",y, x)
    return poses

def interpolate_to_wgs84(local_point, poses):
    """
    Interpolates a local reference point to WGS84 coordinates using the three points in poses.
    
    Args:
        local_point (list): Local coordinates to be converted.

    Returns:
        list: WGS84 coordinates.
    """
    wgs84_coords = np.array([pose["wgs84"] for pose in poses])
    wgs84_mean = wgs84_coords.mean(axis=0)
    weights = get_weights(local_point, poses)
    
    interpolated_wgs84 = wgs84_mean + np.dot(weights, wgs84_coords - wgs84_mean)

    return interpolated_wgs84



def convert_to_wgs84(tx, ty, tz, poses = poses):
    """
    Converts local coordinates to WGS84 coordinates.
    """
    local_point = np.array([tx, ty, tz])
    wgs84_point = interpolate_to_wgs84(local_point, poses)
    return wgs84_point
    
    
def convert_file(input = "LIN_poses.txt", output = "output.txt", poses = poses):
    """Convert a whole file of poses (that need to be product with lamar-benchmarl) to WGS84 coordinates.

    Args:
        input (str, optional): path of input poses.txt. Defaults to "LIN_poses.txt".
        output (str, optional): path of output file. Defaults to "output.txt".
        
    """
    local_points = []
    column2_values = []
    with open(input, "r", encoding="utf-8") as file:
        for line in file:
            if not line.strip() or line.startswith("#") or line.startswith("//"):
                continue
            parts = line.split(",")
            column2_values.append(parts[1].strip())
            local_points.append([float(parts[6]), float(parts[7]), float(parts[8])])

    with open(output, "w", encoding="utf-8") as file:
        file.write("# Interpolated WGS84 points with column2\n")
        file.write("# Format: column2, latitude, longitude, elevation\n")
        for local_point, column2 in zip(local_points, column2_values):
            wgs84_point = interpolate_to_wgs84(local_point, poses)
            file.write(f"{column2}, {wgs84_point[0]}, {wgs84_point[1]}, {wgs84_point[2]}\n")

    print(f"Converted points with column2 have been saved to {output}")
    

if __name__ == "__main__":
        
    tx, ty, tz = 87.19216054872965, -58.229433377117175, -1.8841856889721933
    wgs84_coords = convert_to_wgs84(tx, ty, tz)
    print(f"WGS84 Coordinates: {wgs84_coords}")

    convert_file()
