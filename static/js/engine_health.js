const chart_object = {
    type: 'bar',
    data: {
        labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
        datasets: [{
            label: '# of Votes',
            data: [12, 19, 3, 5, 2, 3],
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                'rgba(255, 206, 86, 0.2)',
                'rgba(75, 192, 192, 0.2)',
                'rgba(153, 102, 255, 0.2)',
                'rgba(255, 159, 64, 0.2)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(255, 159, 64, 1)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        },
        plugins: {
            legend: {
                display: false
            }
        }
    },
    plugins: [{
        beforeInit: (chart, args, options) => {
            // Make sure we're applying the legend to the right chart
            // if (chart.canvas.id === "chart-id") {
                const ul = document.createElement('ul');
                chart.data.labels.forEach((label, i) => {
                    ul.innerHTML += `
                        <li>
                          <span style="background-color: ${chart.data.datasets[0].backgroundColor[i]}">
                            ${chart.data.datasets[0].data[i]}
                          </span>
                          ${label}
                        </li>
                    `;
                });

                return document.getElementById("custom-legend").appendChild(ul);
            // }


        }
    }]
}

$(document).on('vue_init', () => {
    window.test_chart = new Chart('tst', chart_object)
})