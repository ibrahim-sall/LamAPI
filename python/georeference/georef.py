import numpy as np
#from .z_interpolation import get_elevation

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

def get_elevation(las_file, x, y):
    """
    Extracts the elevation (Z) value for a given (X, Y) coordinate from a LAS file.

    Args:
        las_file (str): Path to the LAS file. _________EPSG 2056________
        x (float): X coordinate (longitude or easting)._________EPSG 4326________
        y (float): Y coordinate (latitude or northing)._________EPSG 4326________

    Returns:
        float: Elevation (Z) value at the given (X, Y) coordinate.
    """
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    x, y = transformer.transform(x, y)
    with laspy.open(las_file) as las:
        closest_point = None
        min_distance = float('inf')

        print("Starting to process LAS file...")
        total_points = las.header.point_count
        chunk_size = 10_000
        num_chunks = (total_points // chunk_size) + (1 if total_points % chunk_size != 0 else 0)

        for points in tqdm(las.chunk_iterator(chunk_size), total=num_chunks, desc="Processing chunks"):
            coords = np.vstack((points.x, points.y, points.z)).T
            distances = np.sqrt((coords[:, 0] - x)**2 + (coords[:, 1] - y)**2)
            closest_idx = np.argmin(distances)

            if distances[closest_idx] < min_distance:
                min_distance = distances[closest_idx]
                closest_point = coords[closest_idx]

        if closest_point is not None:
            print(f"Closest point found at distance {min_distance:.2f}")
            return closest_point[2]
        else:
            print("No closest point found.")
            return None


def computeOrthoBase(P1,P2,P3): 
    """Compute the orthonormal base of the three points in 3D space.
    Args:
        P1 (_type_): 
        P2 (_type_): _description_
        P3 (_type_): _description_

    Returns:
        _type_: _description_
    """
    vec12 = P2 - P1
    vec12 /= np.linalg.norm(vec12)
    vec13 = P3 - P1
    vec13 /= np.linalg.norm(vec13) 

    Ri = 0.5*(vec12 - vec13)
    Rj = 0.5*(vec12 + vec13)
    Rk = np.cross(Ri,Rj)

    return np.array([Ri,Rj,Rk]).transpose()

def rotation(PtsRelative, PtsAbsolute):
    """Compute rotation matrix between two coordinates systems using two Orthonormal bases.

    Args:
        PtsRelative (np.ndarray): Array of relative points.
        PtsAbsolute (np.ndarray): Array of absolute points.
    Returns:
        Array(3x3): Rotation matrix.
    """
    
    local_base = computeOrthoBase(PtsRelative[0, :], PtsRelative[1, :], PtsRelative[2, :])
    global_base = computeOrthoBase(PtsAbsolute[0, :], PtsAbsolute[1, :], PtsAbsolute[2, :])
    
    return global_base @ np.linalg.inv(local_base)

def scale_factor(PtsRelative, PtsAbsolute):
    """
    Computes the scale factor between two coordinate systems using the distances between points.
    Args:
        PtsRelative (np.ndarray): Array of relative points.
        PtsAbsolute (np.ndarray): Array of absolute points.
    Returns:
        float: Scale factor.
        
    """
    

    dist12r = np.linalg.norm(PtsRelative[1, :] - PtsRelative[0, :])
    dist12a = np.linalg.norm(PtsAbsolute[1, :] - PtsAbsolute[0, :])
    dist13r = np.linalg.norm(PtsRelative[2, :] - PtsRelative[0, :])
    dist13a = np.linalg.norm(PtsAbsolute[2, :] - PtsAbsolute[0, :])

    scale1, scale2 = dist12a / dist12r, dist13a / dist13r

    return 0.5 * (scale1 + scale2)


def solve_system(poses):
    """Estimates the rotation (M) and translation (T) matrices for the system X2 = M * X1 + T + (1+scale)X1.

    Args:
        poses (list): List of dictionaries containing local ("local") and global ("wgs84") points.

    """
    PtsRelative = np.array([poses[i]["local"] for i in range(3)])
    PtsAbsolute = np.array([poses[i]["wgs84"] for i in range(3)])
    
    M = rotation(PtsRelative, PtsAbsolute)
    scale = scale_factor(PtsRelative, PtsAbsolute)
    centrL, centrG = PtsRelative.mean(axis=0), PtsAbsolute.mean(axis=0)
    
    
    tr = centrG - scale * M @ centrL
    
    return M, scale, tr
    


def convert_to_wgs84(local_point, poses = poses):
    """
    Converts local coordinates to WGS84 coordinates.
    Args:
        local_point (list): Local coordinates to be converted.
        poses (list): List of dictionaries containing the reference points.
    Returns:
        list: Converted WGS84 coordinates.
    """
    
    M, scale, tr = solve_system(poses)
    
    
    wgs84_coords = tr + scale * M @ local_point

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
            wgs84_point = convert_to_wgs84(local_point, poses)
            file.write(f"{column2}, {wgs84_point[0]}, {wgs84_point[1]}, {wgs84_point[2]}\n")

    print(f"Converted points with column2 have been saved to {output}")


def evaluate_precision(poses):
    print("\n--- Évaluation de la précision ---")
    errors = []
    for i, pose in enumerate(poses):
        predicted = convert_to_wgs84(np.array(pose["local"]), poses)
        actual = np.array(pose["wgs84"])
        error = np.linalg.norm(predicted - actual)
        errors.append(error)
        print(f"Point {i+1} - Erreur: {error:.4f} m")
    
    mean_error = np.mean(errors)
    max_error = np.max(errors)
    std_error = np.std(errors)
    rms_error = np.sqrt(np.mean(np.square(errors)))

    print("\nRésumé des erreurs :")
    print(f"Erreur moyenne : {mean_error:.4f} m")
    print(f"Erreur max     : {max_error:.4f} m")
    print(f"Écart-type     : {std_error:.4f} m")
    print(f"Erreur RMS     : {rms_error:.4f} m")

if __name__ == "__main__":
    tx, ty, tz = 87.19216054872965, -58.229433377117175, -1.8841856889721933
    local_point = np.array([tx, ty, tz])
    
    print("Local point:", local_point) 
    print("WGS84 estimé:", convert_to_wgs84(local_point))

    # Test de précision sur les points de référence
    evaluate_precision(poses)


    #convert_file()
