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


def solve_system(poses):
    """Estime les matrices de rotation (R) et de translation (T) pour le système X2 = R * X1 + T.

    Args:
        poses (list): Liste de dictionnaires contenant les points locaux ("local") et globaux ("wgs84").

    Returns:
        tuple: Matrice de rotation R (3x3) et vecteur de translation T (3x1).
    """
    poses = elevation()
    X1 = np.array([pose["local"] for pose in poses]).T 
    X2 = np.array([pose["wgs84"] for pose in poses]).T 

    T = np.mean(X2 - X1, axis=0)
    
    n = len(X1)
    
    X1 = X1 - np.mean(X1, axis=0)
    X2 = X2 - np.mean(X2, axis=0)

    C = np.dot(X1.T, X2) / n
    
    U, _, Vt = np.linalg.svd(C)
    R = np.dot(Vt.T, U.T)

    
    return R, T




def convert_to_wgs84(local_point, poses = poses):
    """
    Converts local coordinates to WGS84 coordinates.
    """
    R, T = solve_system(poses)
    
    
    wgs84_coords = R @ local_point + T + local_point

    return wgs84_coords

    
    
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
            wgs84_point =convert_to_wgs84(local_point, poses)
            file.write(f"{column2}, {wgs84_point[0]}, {wgs84_point[1]}, {wgs84_point[2]}\n")

    print(f"Converted points with column2 have been saved to {output}")
    

if __name__ == "__main__":
        
    tx, ty, tz = 87.19216054872965, -58.229433377117175, -1.8841856889721933
    local_point = np.array([tx, ty, tz])
    wgs84_coords = convert_to_wgs84(local_point)
    print(f"WGS84 Coordinates: {wgs84_coords}")

    #convert_file()
