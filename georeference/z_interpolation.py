import laspy
from pyproj import Transformer
from scipy.spatial import Delaunay
import numpy as np
import os
import laspy
import numpy as np
from scipy.spatial import cKDTree
from tqdm import tqdm

def convert_las_to_wgs84(input_las, output_txt):
    """
    Convertit les coordonnées d'un fichier LAS (EPSG:2056) en WGS84 et extrait les coordonnées Z.

    Args:
        input_las (str): Chemin vers le fichier LAS en EPSG:2056.
        output_txt (str): Chemin vers le fichier de sortie contenant les coordonnées WGS84.
    """
    transformer = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)

    with laspy.open(input_las) as las_file:
        las = las_file.read()
        x, y, z = las.x, las.y, las.z

        lon, lat, alt = transformer.transform(x, y, z)

        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("# Longitude, Latitude, Altitude (WGS84)\n")
            for lon_val, lat_val, alt_val in zip(lon, lat, alt):
                f.write(f"{lon_val}, {lat_val}, {alt_val}\n")

    print(f"Conversion terminée. Les coordonnées WGS84 ont été enregistrées dans {output_txt}")

def interpolate_z_from_xy(xy_points, query_points):
    """
    Interpole les coordonnées Z à partir des coordonnées X et Y en utilisant une interpolation triangulaire.

    Args:
        xy_points (np.ndarray): Tableau de points (X, Y, Z) où Z est connu.
        query_points (np.ndarray): Tableau de points (X, Y) pour lesquels Z doit être interpolé.

    Returns:
        np.ndarray: Coordonnées Z interpolées pour les points de requête.
    """
    xy = xy_points[:, :2] 
    z = xy_points[:, 2] 

    delaunay = Delaunay(xy)

    simplices = delaunay.find_simplex(query_points)

    interpolated_z = np.full(len(query_points), np.nan)

    for i, simplex in enumerate(simplices):
        if (simplex == -1):
        
            continue
        vertices = delaunay.simplices[simplex]
        bary_coords = delaunay.transform[simplex, :2].dot(query_points[i] - delaunay.transform[simplex, 2])
        bary_coords = np.append(bary_coords, 1 - bary_coords.sum())
        interpolated_z[i] = np.dot(bary_coords, z[vertices])

    return interpolated_z

def get_elevation(las_file, x, y):
    """
    Extracts the elevation (Z) value for a given (X, Y) coordinate from a LAS file.

    Args:
        las_file (str): Path to the LAS file.
        x (float): X coordinate (longitude or easting).
        y (float): Y coordinate (latitude or northing).

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


if __name__ == "__main__":
    input_las = "/mnt/lamas/data/MNT/2683_1247.las"
    output_txt = "/mnt/lamas/data/MNT/2683_1247_wgs84.txt"

    if not os.path.exists(output_txt):
        convert_las_to_wgs84(input_las, output_txt)
    else:
        print(f"Le fichier de sortie {output_txt} existe déjà. Conversion non nécessaire.")

    # with laspy.open(input_las) as las_file:
    #     las = las_file.read()
    #     xy_points = np.column_stack((las.x, las.y, las.z))


    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    
    query_points = np.array([[47.371298, 8.5411435], [47.37191374212907, 8.54109663480698], [47.37134209318172, 8.540975215978614]])
    
    query_points_2056 = np.array([transformer.transform(lon, lat) for lon, lat in query_points])

    for i, (x, y) in enumerate(query_points_2056):
        z = get_elevation(input_las, x, y)
        print(f"Elevation at WGS84 ({query_points[i][0]}, {query_points[i][1]}) / EPSG:2056 ({x}, {y}) is: {z}")

