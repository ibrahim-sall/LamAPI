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

def ComputeOrthoBase(P1,P2,P3): 
  
  vec12 = P2 - P1
  vec12 /= np.linalg.norm(vec12)
  vec13 = P3 - P1
  vec13 /= np.linalg.norm(vec13) 

  Ri = 0.5*(vec12 - vec13)
  Rj = 0.5*(vec12 + vec13)
  Rk = np.cross(Ri,Rj)


  return np.array([Ri,Rj,Rk]).transpose()

if __name__ == "__main__":
    
    P1_local = np.array(poses[0]["local"])
    P2_local = np.array(poses[1]["local"])
    P3_local = np.array(poses[2]["local"])

    P1_global = np.array(poses[0]["wgs84"])
    P2_global = np.array(poses[1]["wgs84"])
    P3_global = np.array(poses[2]["wgs84"])

    local_base = ComputeOrthoBase(P1_local, P2_local, P3_local)
    global_base = ComputeOrthoBase(P1_global, P2_global, P3_global)
    
    M = global_base @ np.linalg.inv(local_base)
    
    PtsRelative = np.array([P1_local, P2_local, P3_local])
    PtsAbsolute = np.array([P1_global, P2_global, P3_global])
    

    dist12r = np.linalg.norm(PtsRelative[1, :] - PtsRelative[0, :])
    dist12a = np.linalg.norm(PtsAbsolute[1, :] - PtsAbsolute[0, :])
    dist13r = np.linalg.norm(PtsRelative[2, :] - PtsRelative[0, :])
    dist13a = np.linalg.norm(PtsAbsolute[2, :] - PtsAbsolute[0, :])

    scale1 = dist12a / dist12r
    scale2 = dist13a / dist13r
    scale = 0.5 * (scale1 + scale2)
    print(scale1, scale2, scale)
    
    centrL = np.array([0,0,0],dtype=float)
    centrG = np.array([0,0,0],dtype=float)
    for i in range(3):
        centrL[0] += PtsRelative[i,0]
        centrL[1] += PtsRelative[i,1]
        centrL[2] += PtsRelative[i,2]
        centrG[0] += PtsAbsolute[i,0]
        centrG[1] += PtsAbsolute[i,1]
        centrG[2] += PtsAbsolute[i,2]

    centrL /= 3
    centrG /= 3

    tr = centrG - scale * M @ centrL
        
    tx, ty, tz = 87.19216054872965, -58.229433377117175, -1.8841856889721933
    local_point = np.array([tx, ty, tz])
    
    wgs84_point = tr + scale * M @ local_point
    print(wgs84_point)

    #convert_file()
