# LamAPI
This repo contains our school's project aiming to build a Web service that compute GeoPose from user's infos

## lamar-benchmark

We provide a docker subdirectory with the dockerfile from lamar-benchmark and a README ['How to set-up server?'](docker/DOCKER.md) to set-up the server from distant image (that's the better solution for installation stability).

## API-geopose

This is the visual when the user arrives on the site.
It has the possibility to enter an image to geopose, and provide options files to improve processing.
![Alt text](./images/web_vide.png?raw=true "Page home")

The image and name of the selected folder is displayed to allow the user to check their actions.
File names must be:
images.txt, wifi.txt, bt.txt and sensors.txt.
![Alt text](./images/web_data.png?raw=true "Image et data intégrée")

Once the calculation is finished, the GeoPose is displayed and the position is shown on a Leaflet map.
There is a button to access the location on Street Map.
![Alt text](./images/web_result.png?raw=true "Result")