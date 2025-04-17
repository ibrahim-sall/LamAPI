import os 
from server_func.to_capture import *

def write_data(imgdata, geo_pose_request):
    """
    Écrit les données d'image et les lectures des capteurs dans le répertoire de sortie.

    Args:
        imgdata (bytes): Les données de l'image en bytes.
        geo_pose_request (GeoPoseRequest): La requête GeoPose contenant les lectures des capteurs.
    """

    justId = geo_pose_request.sensorReadings.cameraReadings[0].sensorId.split("/")[0]

    try:
        data_dir = os.getenv("DATA_DIR")
        output_dir = f"{data_dir}/{args.dataset}/sessions/query_{geo_pose_request.id}"
        proc_dir = f"{output_dir}/proc"
        raw_dir = f"{output_dir}/raw_data/{justId}/images"
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(proc_dir, exist_ok=True)
        os.makedirs(raw_dir, exist_ok=True)
        print(f"Répertoire créé : {output_dir}")
    except Exception as e:
        print(f"Erreur lors de la création du répertoire : {e}")
        raise

    # Création fichier subsessions
    query_path = f"{proc_dir}/subsessions.txt"
    with open(query_path, "w") as query_file:
        query_file.write(f"{justId}\n")

    try:
        image_path = f"{raw_dir}/{geo_pose_request.sensorReadings.cameraReadings[0].timestamp}.jpg"
        with open(image_path, 'wb') as image_file:
            image_file.write(imgdata)
            print(f"Image écrite : {image_path}")
    except Exception as e:
        print(f"Erreur lors de l'écriture de l'image : {e}")
        raise

    sensor_readings = {
        "bluetoothReadings": {
            "filename": "bt.txt",
            "header": "# timestamp, sensor_id, mac_addr, rssi_dbm, name\n",
            "line_format": lambda reading: [
                f"{reading.timestamp}, {reading.sensorId}, {mac}, {rssi}, {reading.name or ''}\n"
                for mac, rssi in zip(reading.address, reading.RSSI)
            ]
        },
        "wifiReadings": {
            "filename": "wifi.txt",
            "header": "# timestamp, sensor_id, mac_addr, frequency_khz, rssi_dbm, name, scan_time_start_us, scan_time_end_us\n",
            "line_format": lambda reading: [
                f"{reading.timestamp}, {reading.sensorId}, {bssid}, {freq}, {rssi}, {reading.SSID or ''}, {start}, {end}\n"
                for bssid, freq, rssi, start, end in zip(
                    reading.BSSID, reading.frequency, reading.RSSI, reading.scanTimeStart, reading.scanTimeEnd
                )
            ]
        },
        "cameraReadings": {
            "filename": "images.txt",
            "header": "# timestamp, sensor_id, image_path\n",
            "line_format": lambda reading: [
                f"{reading.timestamp}, {reading.sensorId}, {justId}/images/{reading.timestamp}.jpg\n"
            ]
        }
    }

    for attribute, details in sensor_readings.items():
        file_path = f"{output_dir}/{details['filename']}"
        readings = getattr(geo_pose_request.sensorReadings, attribute, [])

        if readings or attribute == "cameraReadings":
            print(f"Traitement des données pour {attribute} :")
            try:
                with open(file_path, 'w', encoding='utf-8') as sensor_file:
                    sensor_file.write(details['header'])
                    if readings:
                        for reading in readings:
                            lines = details['line_format'](reading)
                            sensor_file.writelines(lines)
                    print(f"Fichier écrit : {file_path}")
            except Exception as e:
                print(f"Erreur lors de l'écriture du fichier {details['filename']} : {e}")
                raise
        else:
            print(f"Aucune donnée trouvée pour {attribute}, fichier ignoré.")

    # Création fichier queries
    query_path = f"{output_dir}/queries.txt"
    with open(query_path, "w") as query_file:
        query_file.write(f"{geo_pose_request.sensorReadings.cameraReadings[0].timestamp}, {geo_pose_request.sensorReadings.cameraReadings[0].sensorId}\n")

    # Création fichier sensors
    query_path = f"{output_dir}/sensors.txt"
    with open(query_path, 'w') as sensor_file:
        sensor_file.write("# sensor_id, name, sensor_type, [sensor_params]+\n")

        if hasattr(geo_pose_request.sensorReadings, "cameraReadings") and geo_pose_request.sensorReadings.cameraReadings:
            cam = geo_pose_request.sensorReadings.cameraReadings[0]

            sensor_id = cam.sensorId
            name = f"phone camera for timestamp {cam.timestamp}"
            sensor_type = "camera"
            width, height = cam.size if cam.size else (0, 0)
            model = cam.params.model if hasattr(cam.params, "model") else ""
            params = cam.params.modelParams if hasattr(cam.params, "modelParams") else ""

            param_str = ', '.join(str(p) for p in params)
            cam_line = f"{sensor_id}, {name}, {sensor_type}, {model}, {width}, {height}"
            if param_str:
                cam_line += f", {param_str}"
            cam_line += "\n"

            sensor_file.write(cam_line)

        # Check if 'sensors' attribute exists before accessing it
        if hasattr(geo_pose_request, "sensors") and geo_pose_request.sensors:
            for sensor in geo_pose_request.sensors:
                if hasattr(sensor, "type") and sensor.type == SensorType.BLUETOOTH:
                    bt_line = f"{sensor.id}, Apple bluetooth sensor, bluetooth\n"
                    sensor_file.write(bt_line)

        return f"query_{geo_pose_request.id}"
