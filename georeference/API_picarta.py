import os
from picarta import Picarta

api_token = os.environ['API_KEY']

localizer = Picarta(api_token)

def process_images(image_paths, center_latitude=None, center_longitude=None, radius=None, top_k=10):
    """
    Process a list of images and return a matrix of coordinates with their names.

    Args:
        image_paths (list): List of image file paths or URLs.
        center_latitude (float): Center latitude for the search area (optional).
        center_longitude (float): Center longitude for the search area (optional).
        radius (float): Radius of the search area in kilometers (optional).
        top_k (int): Number of top results to return for each image.

    Returns:
        list: A matrix where each row contains the image name and its coordinates.
    """
    results_matrix = []

    for img_path in image_paths:
        try:
            result = localizer.localize(
                img_path=img_path,
                top_k=top_k,
                center_latitude=center_latitude,
                center_longitude=center_longitude,
                radius=radius
            )
            if result and "ai_lat" in result and "ai_lon" in result:
                coordinates = [result["ai_lat"], result["ai_lon"]]
                results_matrix.append([img_path, coordinates])
            else:
                results_matrix.append([img_path, "No coordinates found"])
        except Exception as e:
            results_matrix.append([img_path, f"Error: {str(e)}"])

    return results_matrix

if __name__ == "__main__":
    image_paths = [
        os.path.join(os.getcwd(), f) for f in os.listdir(os.getcwd())
        if os.path.isfile(os.path.join(os.getcwd(), f)) and f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    results = process_images(
        image_paths=image_paths,
        center_latitude=47.383,
        center_longitude=8.537,
        radius=10
    )

    for row in results:
        print(row)