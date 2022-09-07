// const chart_object = {
//     type: 'bar',
//     data: {
//         labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
//         datasets: [{
//             label: '# of Votes',
//             data: [12, 19, 3, 5, 2, 3],
//             backgroundColor: [
//                 'rgba(255, 99, 132, 0.2)',
//                 'rgba(54, 162, 235, 0.2)',
//                 'rgba(255, 206, 86, 0.2)',
//                 'rgba(75, 192, 192, 0.2)',
//                 'rgba(153, 102, 255, 0.2)',
//                 'rgba(255, 159, 64, 0.2)'
//             ],
//             borderColor: [
//                 'rgba(255, 99, 132, 1)',
//                 'rgba(54, 162, 235, 1)',
//                 'rgba(255, 206, 86, 1)',
//                 'rgba(75, 192, 192, 1)',
//                 'rgba(153, 102, 255, 1)',
//                 'rgba(255, 159, 64, 1)'
//             ],
//             borderWidth: 1
//         }]
//     },
//     options: {
//         scales: {
//             y: {
//                 beginAtZero: true
//             }
//         },
//         plugins: {
//             legend: {
//                 display: false
//             }
//         }
//     },
//     plugins: [{
//         beforeInit: (chart, args, options) => {
//             // Make sure we're applying the legend to the right chart
//             // if (chart.canvas.id === "chart-id") {
//             const ul = document.createElement('ul');
//             chart.data.labels.forEach((label, i) => {
//                 ul.innerHTML += `
//                         <li>
//                           <span style="background-color: ${chart.data.datasets[0].backgroundColor[i]}">
//                             ${chart.data.datasets[0].data[i]}
//                           </span>
//                           ${label}
//                         </li>
//                     `;
//             });
//
//             return document.getElementById("custom-legend").appendChild(ul);
//             // }
//
//
//         }
//     }]
// }

// $(document).on('vue_init', () => {
//     window.test_chart = new Chart('tst', chart_object)
// })
const formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

window.engine_health = {
    reload: () => {
        const params = window.engine_health.get_params()
        Object.values(window.engine_health.charts).forEach(async i => {
            const resp = await fetch(i.url + params)
            if (resp.ok) {
                i.chart.data = await resp.json()
                i.chart.options.scales.x.min = new Date(params.get('start_time')).valueOf()
                i.chart.options.scales.x.max = new Date(params.get('end_time')).valueOf()
                i.chart.update()
            } // todo: handle resp not ok
        })
    },
    get_params: () => {
        const {
            build_id,
            test_name,
            lg_type,
            sampler_type,
            start_time,
            end_time,
            aggregator,
            slider
        } = vueVm.registered_components.summary
        return new URLSearchParams({
            build_id,
            test_name,
            lg_type,
            sampler: sampler_type,
            start_time,
            end_time,
            aggregator,
            low_value: slider.low,
            high_value: slider.high
        })
    },
    charts: {}
}


$(document).on('vue_init', async () => {
    window.engine_health.charts.load = {
    chart: new Chart('engine_health_load', {
        type: 'line',
        // parsing: false,
        normalized: true,
        responsive: true,
        options: {
            scales: {
                y: {
                    min: 0,
                    // max: 100,
                    type: 'linear',
                    ticks: {
                        count: 6,
                        padding: 28
                    }
                },
                x: {
                    type: 'time',
                    grid: {
                        display: false
                    },
                    display: false
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'LOAD',
                    align: 'start',
                    fullSize: false
                },
            },
        },
    }),
    url: '/api/v1/backend_performance/charts/engine_health/load?'
}
    window.engine_health.charts.cpu = {
        chart: new Chart('engine_health_cpu', {
            type: 'line',
            // parsing: false,
            normalized: true,
            responsive: true,
            options: {
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        // suggestedMax: 100,
                        type: 'linear',
                        ticks: {
                            count: 6,
                            callback: (value, index, ticks) => {
                                return `${value}%`
                            },
                            padding: 15
                        },
                    },
                    x: {
                        type: 'time',
                        grid: {
                            display: false
                        },
                        display: false
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: 'CPU',
                        align: 'start',
                        fullSize: false
                    },
                },
            },
        }),
        url: '/api/v1/backend_performance/charts/engine_health/cpu?'
    }
    window.engine_health.charts.memory = {
        chart: new Chart('engine_health_memory', {
            type: 'line',
            normalized: true,
            responsive: true,
            options: {
                scales: {
                    y: {
                        type: 'linear',
                        min: 0,
                        // suggestedMax: 46600000000,
                        ticks: {
                            count: 6,
                            callback: (value, index, ticks) => {
                                return formatBytes(value)
                            }
                        }
                    },
                    x: {
                        type: 'time',
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: 'MEMORY',
                        align: 'start',
                        fullSize: false
                    },
                },
            }
        }),
        url: '/api/v1/backend_performance/charts/engine_health/memory?'
    }
    window.engine_health.reload()
})