async function fetchData() {
    const url = 'http://127.0.0.1:5000/devicesData?id=92202993';
    try {
        const response = await fetch(url);

        // Vérifie si la réponse est correcte
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }

        // Récupère et parse les données JSON
        var data = await response.json();
        var count = Object.keys(data).length;
        // Affiche les données dans la console
        //console.log(count);
        return [count, data];
        
    } catch (error) {
        console.error('Erreur lors de la récupération des données:', error);
    }
}

async function sliceData() {
    var [lastLotNumber, data] = await fetchData();
    const lastTimestamp = data[lastLotNumber].timestamp; // Récupérer le timestamp du dernier lot
    const timestampLimit = lastTimestamp - 60;  // Définir le timestamp limite pour les 60 dernières secondes
    const ifHcOctetsinValues = []; // Créer un tableau pour stocker les valeurs ifHcOctetsin des 60 dernières secondes
    const timestamps = [];
    // Parcourir les lots de données en partant du dernier lot
    for (let i = lastLotNumber; i >= 0; i--) {
        if (data[i]) {
            const currentTimestamp = data[i].timestamp;

            // Vérifier si le timestamp du lot est dans les 60 dernières secondes
            if (currentTimestamp >= timestampLimit) {
                // Ajouter la valeur ifHcOctetsin et le timestamp aux tableaux
                if (data[i].ifHcOctetsin){
                    ifHcOctetsinValues.push(data[i].ifHcOctetsin);
                }
                else {
                    ifHcOctetsinValues.push(-1);
                }
                timestamps.push(currentTimestamp);
            } else {
                if (data[i].ifHcOctetsin){
                    ifHcOctetsinValues.push(data[i].ifHcOctetsin);
                }
                else {
                    ifHcOctetsinValues.push(-1);
                }
                timestamps.push(currentTimestamp);
                // Si le timestamp est en dehors de la plage, arrêter la boucle
                break;
            }
        }
    }
    //console.log(ifHcOctetsinValues, timestamps)
    return [timestamps, ifHcOctetsinValues];// Retourner les valeurs récupérées
}

function Creategraph(ctx){
    sliceData().then(function(measurement) {
        var timestamps = measurement[0]; // Accéder à test1 une fois que la promesse est résolue
        var data = measurement[1];
        console.log(timestamps, data); // Affiche test1 et test2
        const dataset1 = {
          labels: timestamps,
          datasets: [{
            label: 'IfHCInOctets',
            data: data,
            fill: false,
            borderColor: 'rgb(75, 192, 192)',
          }]
        };
        chart = new Chart(ctx, {
          type: 'line',
          data: dataset1,
          options: {
            scales: {
              y: {
                beginAtZero: true
              }
            }
          }
        });
    }).catch(function(error) {
        console.error("Erreur:", error); // Gérer les erreurs si nécessaire
    });
}

async function Updategraph(){
    var [newlabels, newdata] = await sliceData();

    chart.data.labels = newlabels;
    chart.data.datasets[0].data = newdata;
    chart.update();
    console.log(newlabels, newdata);
}