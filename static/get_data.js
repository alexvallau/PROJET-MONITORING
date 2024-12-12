async function fetchData(id) { 
    // Cette fonction retourne uniquemet l'entiereté des données (data) ainsi que le compte totale de data récolté (count)
    //pour une machine dont l'id est donnée en paramètre, les outputs sont ressorti sous la forme d'un tableau
    const url = '/devicesData?id='+String(id);
    //console.log(url);
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
        //console.log(count, data);
        return [count, data];
        
    } catch (error) {
        console.error('Erreur lors de la récupération des données:', error);
    }
}

async function sliceData(id, attribut, duree) {
    var [lastLotNumber, data] = await fetchData(id); // appel fetchdata pour récupérer les données (=data) et le compteur de donnée (=lastlotnumber)
    const lastTimestamp = data[lastLotNumber].timestamp;
    console.log("l'id est "+id) // Récupérer le timestamp du dernier lot
    const timestampLimit = lastTimestamp - duree;  // Définir le timestamp limite pour les X dernières secondes
    
    const attributValues = []; // Créer un tableau pour stocker les valeurs attribut des 60 dernières secondes
    const timestamps = [];

    // Parcourir les lots de données en partant du dernier lot
    for (let i = lastLotNumber; i > 1; i--) {
        if (data[i]) {
            const currentTimestamp = data[i].timestamp;

            // Vérifier si le timestamp du lot est dans les 60 dernières secondes
            if (currentTimestamp >= timestampLimit) {
                // Ajouter la valeur attributname et le timestamp aux tableaux
                if (data[i][attribut]){
                    attributValues.unshift(data[i][attribut] || -1);
                }
                timestamps.unshift(currentTimestamp);
            } else {
                if (attribut == "ifHcOctetsin" || attribut == "ifHcOctetsOut"){
                    if (data[i][attribut]){
                        attributValues.unshift(data[i][attribut] || -1);
                    }
                    timestamps.unshift(currentTimestamp);
                }
                // Si le timestamp est en dehors de la plage, arrêter la boucle
                break;
            }
        }
    }
    //console.log(attributValues, timestamps)
    return [timestamps, attributValues];// Retourner les valeurs récupérées
}

function adaptData(attribut, timestamps, data){
    //Traitement des valeurs
    var values = [];
    if(attribut == "ifHcOctetsin" || attribut == "ifHcOctetsOut"){
        var value1, value2, timer1, timer2, diff, speed;
        for ( let index = 1; index < data.length; index ++){
            value1 = data[index-1];
            value2 = data[index];
            timer1 = timestamps[index-1];
            timer2 = timestamps[index];
            diff = timer2 - timer1;
            if (value2 < value1){
                value = (value2 - value1 + 18446744073709599999n);
            } else {
                var value = value2 - value1;
            }
            speed = value/diff;
            values.push(speed*8/1000);
        }
    }else {
        for ( let index = 0; index < data.length; index ++){
            values.push(data[index]/40000)
        }
    }

   // Traitement des Timers
    var timers = [];
    var last_timestamp = timestamps[timestamps.length-1];
    for ( each_timer of timestamps){
        timers.push(last_timestamp - each_timer);
    }
    if(attribut == "ifHcOctetsin" || attribut == "ifHcOctetsOut"){
        timers.pop(timers.length-1);
    }
    //console.log("les resultats sont : ",[timers, values]);
    var valuename;
    switch (attribut){
        case 'ifHcOctetsin':
            valuename = "Débits Entrants(kb/s)"
            break;
        case 'ifHcOctetsOut':
            valuename = "Débits Sortants(kb/s)"
            break;
        case 'RAMRemaining':
            valuename = "Ram Disponible (%)";
        default:
        console.log(`Attribut inconnu`);
    }


    return [timers, values, valuename];
}

function Creategraph(id, attribut, duree, ctx, allcharts){
    //console.log('my'+attribut+'Chart');
    //console.log(id);
    sliceData(id, attribut, duree).then(function(measurement) {
        //console.log("les mesures sont : ", measurement);
        var timers = [];
        var  data = [];
        [timestamps, data, valuename] = adaptData(attribut, measurement[0], measurement[1]);
        //console.log(timestamps, data);
        const dataset1 = {
          labels: timers,
          datasets: [{
            label: valuename,
            data: data,
            fill: false,
            borderColor: 'rgb(75, 192, 192)',
          }]
        };
        if (attribut != "RAMRemaining"){
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
        } else {
            chart = new Chart(ctx, {
                type: 'bar',
                data: dataset1,
                options: {
                  scales: {
                    y: {
                      beginAtZero: false
                    }
                  }
                }
              });
        }
        
        allcharts["chart"+attribut] = chart;
        //console.log(allcharts);
    }).catch(function(error) {
        console.error("Erreur:", error); // Gérer les erreurs si nécessaire
    });
     
}

function Updategraph(id, attribut, duree, chart){
    sliceData(id, attribut, duree).then(function(newmeasurement){
        var newtimers = [];
        var newdata = [];
        [newtimers, newdata] = adaptData(attribut, newmeasurement[0], newmeasurement[1]);
        chart.data.labels = newtimers;
        chart.data.datasets[0].data = newdata;
        chart.update();
        //console.log(chart);
    })
}