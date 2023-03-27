const get_responses_chart = (mount_id, y_label, chartData) => {
    const chart_options = {
        type: 'line',
        data: chartData,
        options: {
            animation: false,
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: false
                }
            },
            scales: {
                x: {
                    type: 'time',
                    grid: {
                        display: true,
                    }
                },
                response_time: {
                    type: 'linear',
                    position: 'left',
                    beginAtZero: true,
                    text: y_label,
                    display: true,
                    grid: {
                        display: true,
                        drawOnChartArea: true,
                        borderDash: [2, 1],
                        color: "#D3D3D3"
                    },
                },
                active_users: {
                    type: 'linear',
                    position: 'right',
                    beginAtZero: true,
                    min: 0,
                    grid: {
                        display: false,
                        drawOnChartArea: true,
                    },
                }
            }
        },
        plugins: []
    }
    return new Chart(mount_id, chart_options);
}