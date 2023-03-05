window.analyticsLine = undefined

function displayAnalytics() {
    $("#preset").hide();
    $("#analytics").show();
    $("#chartjs-custom-legend-analytic").show();
    vueVm.registered_components.analyticFilter.reDrawChart();
}

function getData(scope, request_name) {
    if (!$(`#${request_name}_${scope}`).is(":checked")) {
        findAndRemoveDataSet(`${request_name}_${scope}`);
    } else {
        getDataForAnalysis(scope, request_name)
    }
}

function findAndRemoveDataSet(dataset_name) {
    for (let i = 0; i < analyticsLine.data.datasets.length; i++) {
        if (analyticsLine.data.datasets[i].label === dataset_name) {
            analyticsLine.data.datasets.splice(i, 1);
            analyticsLine.update();
            break;
        }
    }
}

function highlight(e, datasetIndex, chartType) {
    var ci = chartType === 'analytic' ? e.view.analyticsLine : e.view.presetLine;
    ci.data.datasets[datasetIndex].borderWidth = 6;
    ci.update();
}

function lowlight(e, datasetIndex, chartType) {
    var ci = chartType === 'analytic' ? e.view.analyticsLine : e.view.presetLine;
    ci.data.datasets[datasetIndex].borderWidth = 2;
    ci.update();
}

function turnOnAllLine() {
    window.analyticsLine.data.datasets.forEach((item, index) => {
        window.analyticsLine.setDatasetVisibility(index, true)
    })
    // window.analyticsLine.update();
}

function analyticsCanvas(data) {
    window.analyticsLine = new Chart('chart-analytics', {
        type: 'line',
        data: data,
        plugins: [htmlLegendPlugin],
        options: {
            plugins: {
                htmlLegend: {
                    containerID: 'chartjs-custom-legend-analytic',
                },
                legend: {
                    display: false,
                },
                title: {
                    display: false,
                },
            },
            scales: {
                time: {
                    display: true,
                    position: 'left',
                    beginAtZero: true,
                },
                count: {
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    grid: {
                        drawOnChartArea: false,
                    },
                },
            },
        }
    });
}


let filtersBlock = new Map();
let filtersArgsForRequest = new Map();
let analyticLabels = [];

function getDataForAnalysis(metric, request_name) {
    const controller_proxy = vueVm.registered_components.summary;
    const params = new URLSearchParams({
        metric: metric,
        build_id: controller_proxy.build_id,
        test_name: controller_proxy.test_name,
        lg_type: controller_proxy.lg_type,
        sampler: controller_proxy.sampler_type,
        aggregator: controller_proxy.aggregator,
        status: controller_proxy.status_type,
        start_time: controller_proxy.start_time,
        end_time: controller_proxy.end_time,
        low_value: controller_proxy.slider.low,
        high_value: controller_proxy.slider.high,
    })
    request_name.forEach((transaction) => {
        params.append('scope[]', transaction);
    })
    return fetch('/api/v1/backend_performance/charts/requests/data?' + params,{
        method: 'GET'
    }).then((data) => {
        return data.json()
    })
}

function setThresholds() {
    //TODO
    console.log("set current report results as threshold")
}

function downloadReport() {
    //TODO
    console.log("download test report")
}

function shareTestReport() {
    //TODO
    console.log("share test report")
}


function clearAnalyticChart() {
    if (analyticsLine !== null){
        analyticsLine.destroy();
        window.analyticsLine = null;
    }
    document.getElementById('chartjs-custom-legend-analytic').innerHTML = '';
    $('#chart-analytics').hide();
    $('#layout_empty-chart').show();
}