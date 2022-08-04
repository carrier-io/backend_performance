const chartTypes = {
    summary: {
        metric: 'Response time, ms',
        url: '/api/v1/backend_performance/charts/requests/summary'
    },
    average: {
        metric: 'Response time, ms',
        url: '/api/v1/backend_performance/charts/requests/average'
    },
    hits: {
        metric: 'Hits/Requests per second',
        url: '/api/v1/backend_performance/charts/requests/hits'
    },
    analytics: {
        metric: 'Response time, ms',
        url: '/api/v1/backend_performance/charts/requests/data'
    },
}

const analyticScales = {
    yAxes: [{
        type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
        display: true,
        position: "left",
        scaleLabel: {
            display: true,
            labelString: "Response Time, ms"
        },
        id: "time",
    }, {
        type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
        display: true,
        position: "right",
        scaleLabel: {
            display: true,
            labelString: "Count"
        },
        id: "count",
        gridLines: {
            drawOnChartArea: false, // only want the grid lines for one axis to show up
        },
    }],
}

function updateChartUniversal (e, index, component_name) {
    $('#all_checkbox').prop('checked', false);
    const ci = this.vueVm.registered_components[component_name].chartLine
    let curr = ci.data.datasets[index]._meta;
    curr = Object.values(curr)[0];
    curr.hidden = !curr.hidden;
    ci.update();
}

const ResultSummary = {
    components: {
        'dropdown-analytic': DropdownAnalytic,
    },
    props: ['analyticsData', 'instance_name'],
    data() {
        return {
            aggregator: 'Auto',
            statusType: 'All',
            samplerType: 'REQUEST',
            requestUrl: chartTypes['summary'].url,
            requestMetric: chartTypes['summary'].metric,
            chartType: 'summary',
            chartLine: null,
            selectedTransactions: [],
            selectedMetrics: [],
            transactionItems: null,
            metricItems: null,
            low_value: 0,
            high_value: 100,
            selectedItemsLength: 0,
            itemsListLength: 0,
        }
    },
    async mounted() {
        this.transactionItems = Object.keys(this.analyticsData).filter(item => {
            if (item !== 'All' && item !== '') return item
        })
        this.metricItems = Object.keys(this.analyticsData["All"])
        this.chartContext = document.getElementById('chart-canvas').getContext("2d");
        this.createTimePicker();
        if (this.chartType !== 'analytics') {
            const chartData = await this.getChartData();
            this.chartSwitcher(chartData)
        }
    },
    watch: {
        // chartLine: {
        //     deep: true,
        //     handler() {
        //         if (this.chartLine) {
        //             const elements = []
        //             $('#chartjs-custom-legend .custom__checkbox').each((i, ch) => {
        //                 if (ch.id !== "all_checkbox") {
        //                     if ($('#' + ch.id).prop('checked')) elements.push(ch.id)
        //                 }
        //             })
        //             this.selectedItemsLength = elements.length;
        //             if(this.selectedItemsLength === this.itemsListLength) $("#all_checkbox").prop('checked', true)
        //         }
        //     }
        // }
    },
    computed: {
        isAllSelected() {
            return (this.selectedItemsLength < this.itemsListLength) && this.selectedItemsLength > 0
        }
    },
    methods: {
        createTimePicker() {
            const performanceTimePicker = noUiSlider.create($("#vuh-perfomance-time-picker")[0], {
                range: {
                    'min': 0,
                    'max': 100
                },
                start: [this.low_value, this.high_value],
                connect: true,
                format: wNumb({
                    decimals: 0
                }),
            })

            performanceTimePicker.on('set', async (values) => {
                this.low_value = values[0]
                this.high_value = values[1]
                if(this.chartType === 'analytics') {
                    const datasets =[]
                    for (let i = 0; i < this.selectedMetrics.length; i++) {
                        for( let k = 0; k < this.selectedTransactions.length; k++) {
                            const chartData = await this.getChartData(this.selectedMetrics[i], this.selectedTransactions[k])
                            datasets.push(chartData.datasets[0])
                        }
                    }
                    this.chartLine.data.datasets = datasets;
                    this.chartLine.update();
                    document.getElementById('chartjs-custom-legend-analytic').innerHTML = this.chartLine.generateLegend();
                } else {
                    const chartData = await this.getChartData();
                    this.chartSwitcher(chartData)
                }
            });
        },
        async setChartType(type) {
            this.chartType = type;
            this.requestUrl = chartTypes[type].url;
            this.requestMetric = chartTypes[type].metric;
            this.chartLine = null;
            if (type !== 'analytics') {
                $('#all_checkbox').prop('checked', true)
                document.getElementById('chartjs-custom-legend-analytic').innerHTML = '';
            }
            this.selectedTransactions = [];
            this.selectedMetrics = [];
            const chartData = await this.getChartData();
            this.chartSwitcher(chartData)
        },
        selectOrUnselectRequests({ target : { checked}}) {
            if(checked) {
                this.updateCbxState(true)
                this.updateHiddenProperty(false)
            } else {
                this.updateCbxState(false)
                this.updateHiddenProperty(true)
            }
        },
        updateHiddenProperty(hidden) {
            this.chartLine.data.datasets.forEach((item, index) => {
                let curr = item._meta;
                curr = Object.values(curr)[0]
                curr.hidden = hidden
            })
            this.chartLine.update();
        },
        updateCbxState(state) {
            $('.custom__checkbox').each((i, ch) => {
                if (ch.id !== "all_checkbox") {
                    $('#' + ch.id).prop('checked', state);
                }
            })
        },
        async getChartData(analyticMetric = '', TransactionName = '') {
            const requestBody = {
                    build_id: $('meta[property=build_id]').prop('content'),
                    test_name: $('meta[property=test_name]').prop('content'),
                    lg_type: $('meta[property=lg_type]').prop('content'),
                    sampler: $("#sampler").val().toUpperCase(),
                    aggregator: $("#aggregator").val().toLowerCase(),
                    status: $("#status").val().toLowerCase(),
                    start_time: $("#start_time").html(),
                    end_time: $("#end_time").html(),
                    low_value: this.low_value,
                    high_value: this.high_value,
                }
            if ( this.chartType === 'analytics') {
                requestBody['metric'] = analyticMetric;
                requestBody['scope'] = TransactionName;
            }
            return await $.get(
                this.requestUrl,
                requestBody,
                ( data ) => data
            );
        },
        chartSwitcher(chartData) {
            if (this.chartType !== 'analytics') {
                this.drawCanvas(this.requestMetric, chartData);
                document.getElementById('chartjs-custom-legend').innerHTML = this.chartLine.generateLegend();
            } else {
                if (this.chartLine === null || this.chartLine.data.labels.length === 0) {
                    this.drawCanvas(this.requestMetric, chartData);
                } else {
                    this.chartLine.data.datasets.push(chartData.datasets[0]);
                    this.chartLine.update();
                }
                this.onAllLine();
                document.getElementById('chartjs-custom-legend-analytic').innerHTML = this.chartLine.generateLegend();
            }
        },
        setTransactions(payload) {
            this.selectedTransactions = [ ...payload.selectedItems];
            if (payload.clickedItem.isChecked) {
                this.selectedMetrics.forEach(async metric => {
                    const chartData = await this.getChartData(metric, payload.clickedItem.title)
                    this.chartSwitcher(chartData)
                })
            } else {
                this.chartLine.data.datasets = this.chartLine.data.datasets.filter(item => {
                    const label = item.label.split('_').slice(0, -1).join('_');
                    if (payload.clickedItem.title !== label) {
                        return item
                    }
                });
                this.onAllLine();
                document.getElementById('chartjs-custom-legend-analytic').innerHTML = this.chartLine.generateLegend();
                this.chartLine.update();
            }
        },
        setMetrics(payload) {
            this.selectedMetrics = [ ...payload.selectedItems];
            if (payload.clickedItem.isChecked) {
                this.selectedTransactions.forEach(async (transaction) => {
                    const chartData = await this.getChartData(payload.clickedItem.title, transaction)
                    this.chartSwitcher(chartData)
                })
            } else {
                this.chartLine.data.datasets = this.chartLine.data.datasets.filter(item => {
                    const label = item.label.split('_').pop();
                    if (payload.clickedItem.title !== label) {
                        return item
                    }
                });
                this.onAllLine();
                document.getElementById('chartjs-custom-legend-analytic').innerHTML = this.chartLine.generateLegend();
                this.chartLine.update();
            }
        },
        onAllLine() {
            this.chartLine.data.datasets.forEach((item, index) => {
                let curr = item._meta;
                curr = Object.values(curr)[0];
                curr.hidden = false;
            })
            this.chartLine.update();
        },
        drawCanvas(y_label, chartData) {
            const computedScales = this.chartType === 'analytics' ? analyticScales : {
                xAxes: [{
                    gridLines: {
                        display: false
                    }
                }],
                yAxes: [{
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "left",
                    scaleLabel: {
                        display: true,
                        labelString: y_label
                    },
                    id: "response_time",
                    gridLines: {
                        borderDash: [2, 1],
                        color: "#D3D3D3"
                    },
                    ticks: {
                        beginAtZero: true,
                        maxTicksLimit: 10
                    },
                }, {
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "right",
                    gridLines: {
                        display: false
                    },
                    ticks: {
                        beginAtZero: true,
                        maxTicksLimit: 10
                    },
                    id: "active_users",
                }],
            }
            this.chartLine = Chart.Line(this.chartContext, {
                data: chartData,
                options: {
                    responsive: true,
                    hoverMode: 'index',
                    stacked: false,
                    legendCallback: (chart) => {

                        this.itemsListLength = chart.data.datasets.length
                        return chart.data.datasets.map((item, index) => {
                            const computedColor = item.label === 'Active Users' ? 'blue' : item.backgroundColor
                            return `
                                <div class="d-flex mb-3 float-left mr-3">
                                    <label class="mb-0 w-100 d-flex align-items-center custom-checkbox custom-checkbox__multicolor legend-item">
                                        <input class="mx-2 custom__checkbox"
                                            onclick="updateChartUniversal(event, ${chart.legend.legendItems[index].datasetIndex}, 'result-summary')"
                                            id="${chart.legend.legendItems[index].datasetIndex}"
                                            type="checkbox"
                                            checked="true"
                                            style="--cbx-color: ${computedColor}"/>
                                        <span class="custom-chart-legend-span"></span>
                                        ${item.label}
                                    </label>
                                </div>
                            `
                        }).join("")
                    },
                    legend: {
                        display: false,
                        position: 'right',
                        labels: {
                            fontSize: 10,
                            usePointStyle: false
                        }
                    },
                    title: {
                        display: false,
                    },
                    scales: computedScales
                }
            });
        }
    },
    template: `
        <div class="card card-12 p-28 mt-3">
            <div class="d-flex justify-content-between pb-4">
                <h1 class="font-h2">Requests summary</h1>
                <div class="d-flex align-items-center">
                    <div class="complex-list">
                        <select class="selectpicker dropdown-menu__simple" 
                            data-style="btn"
                            id="aggregator"
                            @change="$event => aggregator = $event.target.value">
                            <option>auto</option>
                            <option>1s</option>
                            <option>5s</option>
                            <option>30s</option>
                            <option>1m</option>
                            <option>5m</option>
                            <option>10m</option>
                        </select>
                    </div>
                    <div class="complex-list">
                        <select class="selectpicker dropdown-menu__simple" 
                            data-style="btn" 
                            id="status"
                            @change="$event => statusType = $event.target.value">
                            <option>all</option>
                            <option>ok</option>
                            <option>ko</option>
                        </select>
                    </div>
                    <div class="complex-list mr-3">
                        <select class="selectpicker dropdown-menu__simple" 
                            data-style="btn"
                            id="sampler"
                            @change="$event => samplerType = $event.target.value">
                            <option>REQUEST</option>
                            <option>TRANSACTION</option>
                        </select>
                    </div>
                    <ul class="custom-tabs nav nav-pills mr-3" id="pills-tab" role="tablist">
                        <li class="nav-item" role="presentation">
                            <a id="RT"
                               class="font-h5 font-uppercase active"
                               @click="setChartType('summary')"
                               data-toggle="pill">Responses</a>
                        </li>
                        <li class="nav-item" role="presentation">
                            <a  id="AR"
                                class="font-h5 font-uppercase"
                                @click="setChartType('average')"
                                data-toggle="pill">Average</a>
                        </li>
                        <li class="nav-item" role="presentation">
                            <a  id="TPS"
                                class="font-h5 font-uppercase"  
                                @click="setChartType('hits')"
                                data-toggle="pill">TPS</a>
                        </li>
                        <li class="nav-item" role="presentation">
                            <a  id="AN"
                                class="font-h5 font-uppercase"
                                @click="setChartType('analytics')"
                                data-toggle="pill">Analytics</a>
                        </li>
                    </ul>
                    <button class="btn btn-secondary btn-icon mr-2">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
            <div class="d-flex mt-3">
                <div class="chart flex-grow-1 d-flex flex-column justify-content-between">
                    <div class="flex-grow-1">
                        <canvas id="chart-canvas" class="chart-canvas chartjs-render-monitor"
                            style="display: block; height: 450px; width: 100%;"></canvas>
                    </div>
                    <div class="row pr-4 pl-2">
                        <div class="col">
                            <label class="w-100 mb-0 font-h5 font-semibold">
                                Time picker
                            </label>
                            <div class="w-100">
                                <div class="slider-holder">
                                    <div id="vuh-perfomance-time-picker"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card" style="width:280px; margin-left: 28px">
                    <div v-if="chartType !== 'analytics'">
                        <div class="d-flex flex-column p-3">
                            <label
                                class="mb-0 w-100 d-flex align-items-center custom-checkbox custom-checkbox__multicolor"
                                :class="{ 'custom-checkbox__minus': isAllSelected }"
                                for="all_checkbox">
                                <input
                                    class="mx-2 custom__checkbox"
                                    checked="true" id="all_checkbox" @click="selectOrUnselectRequests"
                                    style="--cbx-color: var(--basic);"
                                    type="checkbox">
                                <span class="w-100 d-inline-block">Select/Unselect all</span>
                            </label>
                        </div>
                        <hr class="my-0">
                        <div id="chartjs-custom-legend" 
                            class="custom-chart-legend d-flex flex-column px-3 py-3"
                            style="height: 400px; overflow: scroll;"
                        ></div>
                    </div>
                    <div v-else>
                        <p class="font-h5 font-bold py-3 px-4 text-gray-800">DATA FILTER</p>
                        <hr class="my-0">
                        <div class="py-3 px-4">
                            <p class="font-h5 font-bold mb-2 text-gray-800">Transaction/Request</p>
                            <dropdown-analytic
                                @select-items="setTransactions"
                                :items-list="transactionItems"
                            ></dropdown-analytic>
                            <p class="font-h5 font-bold mb-2 mt-3 text-gray-800">Metrics</p>
                            <dropdown-analytic
                                @select-items="setMetrics"
                                :items-list="metricItems"
                            ></dropdown-analytic>
                        </div>
                    </div>
                </div>
            </div>
            <div id="chartjs-custom-legend-analytic" style="margin-top: 33px" class="d-grid grid-column-7"></div>
        </div>
    `
}

register_component('result-summary', ResultSummary);
