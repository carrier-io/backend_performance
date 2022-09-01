const get_responses_chart = (mount_id, y_label, chartData) => {
    const chart_options = {
        type: 'line',
        data: chartData,
        options: {
            animation: false,
            responsive: true,
            // hoverMode: 'index',
            interaction: {
                mode: 'point'
            },
            // stacked: false,
            // legendCallback: function (chart) {
            //     var legendHtml = [];
            //     for (var i = 0; i < chart.data.datasets.length; i++) {
            //         if (chart.data.datasets[i].label != "Active Users") {
            //             var cb = '<div class="d-flex mb-3">';
            //             cb += '<label class="mb-0 w-100 d-flex align-items-center custom-checkbox custom-checkbox__multicolor">'
            //             cb += '<input class="mx-2 custom__checkbox" id="' + chart.legend.legendItems[i].datasetIndex + '" type="checkbox" checked="true" style="--cbx-color: ' + chart.data.datasets[i].backgroundColor + ';" '
            //             cb += 'onclick="updateChart(event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ')"/>';
            //             cb += '<span class="custom-chart-legend-span"></span>'
            //             cb += chart.data.datasets[i].label;
            //             cb += '</label></div>'
            //             legendHtml.push(cb);
            //         }
            //     }
            //     return legendHtml.join("");
            // },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: false
                }
            },
            // title: {
            //     display: false,
            // },
            // scales: {
            //     xAxes: [
            //         {
            //             gridLines: {
            //                 display: false
            //             }
            //         }
            //     ],
            //     yAxes: [
            //         {
            //             type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
            //             display: true,
            //             position: "left",
            //             scaleLabel: {
            //                 display: true,
            //                 labelString: y_label
            //             },
            //             id: "response_time",
            //             gridLines: {
            //                 borderDash: [2, 1],
            //                 color: "#D3D3D3"
            //             },
            //             ticks: {
            //                 beginAtZero: true,
            //                 maxTicksLimit: 10
            //             },
            //         },
            //         {
            //             type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
            //             display: true,
            //             position: "right",
            //             gridLines: {
            //                 display: false
            //             },
            //             ticks: {
            //                 beginAtZero: true,
            //                 maxTicksLimit: 10
            //             },
            //             // id: "active_users",
            //         }
            //     ],
            // }
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    display: true,
                    grid: {
                        display: false
                    }
                }
            }
        },
        plugins: []
    }
    // const presetsContext = document.getElementById("chart-requests").getContext("2d");
    return new Chart(mount_id, chart_options);
}