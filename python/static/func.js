function displayImage(event) {
    const preview = document.getElementById('preview');
    const [image] = event.target.files;
    if (image) {
        preview.src = URL.createObjectURL(image);
        preview.style.display = 'block';
    }
}

function displayFolderPath() {
    const input = document.getElementById('folderInput');
    const files = input.files;

    if (files.length === 0) return;

    const firstPath = files[0].webkitRelativePath;
    const folderName = firstPath.split("/")[0];

    document.getElementById("folderPath").innerText = "Dossier sélectionné : " + folderName;
}

let leafletMap = null;
function submitAll() {
    const imageInput = document.getElementById('imageInput');
    const folderInput = document.getElementById('folderInput');

    const imageFile = imageInput.files[0];
    const folderFiles = folderInput.files;

    if (!imageFile || !folderFiles.length) {
        alert("Veuillez importer une image et un dossier.");
        return;
    }

    const formData = new FormData();
    formData.append("image", imageFile);

    for (let i = 0; i < folderFiles.length; i++) {
        formData.append('files', folderFiles[i], folderFiles[i].webkitRelativePath);
    }

    const statusMessage = document.getElementById('statusMessage');
    const progressBar = document.getElementById('progressBar');
    statusMessage.innerText = "Envoi des fichiers au serveur...";
    progressBar.style.display = 'block';

    fetch("/process", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.task_id) {
            statusMessage.innerText = "Traitement en cours...";
            pollTaskStatus(data.task_id);
        } else {
            statusMessage.innerText = "Erreur : Impossible de récupérer l'ID de la tâche.";
        }
    })
    .catch(error => {
        console.error('Erreur de traitement:', error);
        statusMessage.innerText = "Erreur lors de l'envoi des fichiers.";
    });
}

function pollTaskStatus(taskId) {
    const statusMessage = document.getElementById('statusMessage');
    const progress = document.getElementById('progress');

    let progressValue = 0;
    const interval = setInterval(() => {
        fetch(`/geopose/status/${taskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.state === 'PENDING') {
                    statusMessage.innerText = "Traitement en attente...";
                    progressValue = Math.min(progressValue + 10, 95);
                } else if (data.state === 'SUCCESS') {
                    clearInterval(interval);
                    statusMessage.innerText = "Traitement terminé avec succès.";
                    progressValue = 100;
                    processData(data.result);
                } else if (data.state === 'FAILURE') {
                    clearInterval(interval);
                    statusMessage.innerText = "Échec du traitement.";
                    progressValue = 100;
                    console.error("Erreur:", data.error);
                } else {
                    statusMessage.innerText = `Statut : ${data.state}`;
                }

                progress.style.width = `${progressValue}%`;
            })
            .catch(error => {
                clearInterval(interval);
                console.error("Erreur lors du polling:", error);
                statusMessage.innerText = "Erreur lors de la récupération du statut.";
            });
    }, 2000);
}

function handleStatus(response) {
    const statusDiv = document.getElementById('status');
    statusDiv.innerHTML = `<strong>Status Code:</strong> ${response.status}`;

    if (response.status >= 200 && response.status < 300) {
        updateStatusStyle(statusDiv, 'green', 'white');
    } else if (response.status >= 400 && response.status < 500) {
        updateStatusStyle(statusDiv, 'orange', 'black');
    } else if (response.status >= 500) {
        updateStatusStyle(statusDiv, 'red', 'white');
    } else {
        updateStatusStyle(statusDiv, 'gray', 'white');
    }

    return response.json();
}

function updateStatusStyle(element, backgroundColor, color) {
    element.style.backgroundColor = backgroundColor;
    element.style.color = color;
}

function processData(data) {
    const outputDiv = document.getElementById('output');

    const orderedData = {
        "type": data.type,
        "id": data.id,
        "timestamp": data.timestamp,
        "geopose": data.geopose
    };

    const formattedData = JSON.stringify(orderedData, null, 4);

    if (data.output) {
        outputDiv.innerHTML = `<pre>${data.output}</pre>`;
    } else if (data.error) {
        outputDiv.innerHTML = `<pre>${data.error}</pre>`;
    } else {
        outputDiv.innerHTML = `<pre>${formattedData}</pre>`;
    }

    if (data.geopose && data.geopose.position) {
        displayMapAndStreetView(data.geopose.position);
    }
}

function displayMapAndStreetView(position) {
    const { lat, lon } = position;

    if (!lat || !lon) return;

    const mapContainer = document.getElementById('map');
    mapContainer.style.display = 'block';

    if (leafletMap !== null) {
        leafletMap.remove();
        leafletMap = null;
    }

    leafletMap = L.map('map').setView([lat, lon], 15);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(leafletMap);

    L.marker([lat, lon]).addTo(leafletMap)
        .bindPopup('Position GeoPose')
        .openPopup();

    addStreetViewLink(lat, lon);
}

function addStreetViewLink(lat, lon) {
    const linkDiv = document.getElementById("streetview-link");
    linkDiv.innerHTML = "";

    const streetViewUrl = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lon}`;

    const linkBtn = document.createElement("a");
    linkBtn.href = streetViewUrl;
    linkBtn.target = "_blank";
    linkBtn.rel = "noopener noreferrer";
    linkBtn.innerText = "Voir dans Street View";

    linkDiv.appendChild(linkBtn);
}