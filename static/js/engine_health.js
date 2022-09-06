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

$(document).on('vue_init', async () => {
    window.engine_health = {}
    const {
        start_time,
        end_time,
        aggregator,
        test_name,
        build_id
    } = vueVm.registered_components.summary
    const s_params = new URLSearchParams({
        start_time,
        end_time,
        aggregator,
        test_name,
        build_id
    })
    const resp_cpu = await fetch('/api/v1/backend_performance/charts/engine_health/cpu?' + s_params)
    if (resp_cpu.ok) {
        window.engine_health.cpu = new Chart('engine_health_cpu', {
            type: 'line',
            data: await resp_cpu.json(),
            // parsing: false,
            normalized: true,
            responsive: true,
            options: {
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        type: 'linear',
                        ticks: {
                            count: 6,
                            callback: (value, index, ticks) => {
                                return `${value}%`
                            },
                            padding: 14
                        },
                    },
                    x: {
                        min: new Date('2022-09-05T17:13:50.199000Z').valueOf(),
                        max: new Date('2022-09-05T17:32:50.195000Z').valueOf(),
                        type: 'time',
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false,
                        position: 'right'
                    },
                    title: {
                        display: true,
                        text: 'CPU',
                        align: 'start',
                        fullSize: false
                    },
                },
            },
        })
        window.engine_health.disk = new Chart('engine_health_disk', {
            type: 'line',
            data: [],
            // parsing: false,
            normalized: true,
            responsive: true,
            options: {
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        type: 'linear',
                        ticks: {
                            count: 6,
                            padding: 19
                        }
                    },
                    x: {
                        min: new Date('2022-09-05T17:13:50.199000Z').valueOf(),
                        max: new Date('2022-09-05T17:32:50.195000Z').valueOf(),
                        type: 'time',
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false,
                        position: 'right'
                    },
                    title: {
                        display: true,
                        text: 'DISK',
                        align: 'start',
                        fullSize: false
                    },
                },
            },
        })
        window.engine_health.network = new Chart('engine_health_network', {
            type: 'line',
            data: [],
            // parsing: false,
            normalized: true,
            responsive: true,
            options: {
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        type: 'linear',
                        ticks: {
                            count: 6,
                            padding: 19
                        }
                    },
                    x: {
                        min: new Date('2022-09-05T17:13:50.199000Z').valueOf(),
                        max: new Date('2022-09-05T17:32:50.195000Z').valueOf(),
                        type: 'time',
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false,
                        position: 'right'
                    },
                    title: {
                        display: true,
                        text: 'NETWORK',
                        align: 'start',
                        fullSize: false
                    },
                },
            },
        })
    }
    const resp_memory = await fetch('/api/v1/backend_performance/charts/engine_health/memory?' + s_params)
    if (resp_cpu.ok) {
        window.engine_health.memory = new Chart('engine_health_memory', {
            type: 'line',
            data: await resp_memory.json(),
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
                        min: new Date('2022-09-05T17:13:50.199000Z').valueOf(),
                        max: new Date('2022-09-05T17:32:50.195000Z').valueOf(),
                        type: 'time',
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false,
                        position: 'right'
                    },
                    title: {
                        display: true,
                        text: 'MEMORY',
                        align: 'start',
                        fullSize: false
                    },
                },
            }
        })
    }
})