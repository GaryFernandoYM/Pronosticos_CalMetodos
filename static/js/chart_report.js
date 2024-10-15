document.addEventListener("DOMContentLoaded", function () {
    var ctx = document.getElementById('scrapeosChart').getContext('2d');

    // Datos dinámicos para el gráfico
    var labels = JSON.parse(document.getElementById('chart-data').dataset.labels);
    var data = JSON.parse(document.getElementById('chart-data').dataset.data);

    // Crear el gráfico con Chart.js
    var scrapeosChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Total de Scrapeos',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
});
