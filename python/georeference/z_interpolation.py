import laspy
from pyproj import Transformer
import numpy as np
import os
from tqdm import tqdm



def convert_las_to_wgs84(input_las, output_txt):
    """
    Converts the coordinates of a LAS file (EPSG:2056) to WGS84 and extracts the Z coordinates.

    Args:
        input_las (str): Path to the LAS file in EPSG:2056.
        output_txt (str): Path to the output file containing WGS84 coordinates.
    """
    transformer = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)

    with laspy.open(input_las) as las_file:
        las = las_file.read()
        x, y, z = las.x, las.y, las.z

        lon, lat, alt = transformer.transform(x, y, z)

        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("# Lon, Lat, Elevation (WGS84)\n")
            for lon_val, lat_val, alt_val in zip(lon, lat, alt):
                f.write(f"{lon_val}, {lat_val}, {alt_val}\n")

    print(f"Conversion completed. The WGS84 coordinates have been saved in {output_txt}")


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


if __name__ == "__main__":
    input_las = "/mnt/lamas/data/MNT/2683_1247.las"
    output_txt = "/mnt/lamas/data/MNT/2683_1247_wgs84.txt"

    if not os.path.exists(output_txt):
        convert_las_to_wgs84(input_las, output_txt)
    else:
        print(f"The output file {output_txt} already exists. Conversion not required.")

    query_points = np.array([[47.371298, 8.5411435], [47.37191374212907, 8.54109663480698], [47.37134209318172, 8.540975215978614]])


    for i, (x, y) in enumerate(query_points):
        z = get_elevation(input_las, y, x)
        print(f"Elevation at WGS84 ({query_points[i][0]}, {query_points[i][1]}) / EPSG:2056 ({x}, {y}) is: {z}")

