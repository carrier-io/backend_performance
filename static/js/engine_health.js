const formatBytes = (bytes, decimals = 1) => {
    if (bytes === 0) return '0 Bytes'

    const k = 1024
    const dm = decimals < 0 ? 0 : decimals
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + (sizes[i] || 'byte')
}

window.engine_health = {
    reload: async (chart_names = ['all']) => {
        const params = window.engine_health.get_params()
        if (chart_names.includes('all')) {
            const url_all = '/api/v1/backend_performance/charts/engine_health/all?'
            const resp = await fetch(url_all + params)
            if (resp.ok) {
                const charts_data = await resp.json()

                Object.entries(charts_data).forEach(([chart_name, data]) => {
                    const co = window.engine_health.charts[chart_name]
                    if (co !== undefined) {
                        co.chart.data = data
                        // co.chart.options.scales.x.min = new Date(params.get('start_time')).valueOf()
                        // co.chart.options.scales.x.max = new Date(params.get('end_time')).valueOf()
                        co.chart.update()
                    }
                })
                await vueVm.registered_components.engine_health_chart_legend?.load_charts()
            } // todo: handle resp not ok

        } else {
            for (const i of chart_names) {
                const co = window.engine_health.charts[i]
                if (co !== undefined) {
                    const resp = await fetch(co.url + params)
                    if (resp.ok) {
                        co.chart.data = await resp.json()
                        // co.chart.options.scales.x.min = new Date(params.get('start_time')).valueOf()
                        // co.chart.options.scales.x.max = new Date(params.get('end_time')).valueOf()
                        co.chart.update()
                    } // todo: handle resp not ok
                }
            }
        }
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
            // normalized: true,
            responsive: true,
            options: {
                scales: {
                    y: {
                        min: 0,
                        // max: 100,
                        type: 'linear',
                        ticks: {
                            count: 6,
                            padding: 22
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
            // normalized: true,
            responsive: true,
            options: {
                scales: {
                    y: {
                        min: 0,
                        // max: 100,
                        // suggestedMax: 100,
                        type: 'linear',
                        ticks: {
                            count: 6,
                            callback: (value, index, ticks) => {
                                return `${value}%`
                            },
                            padding: 16
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
            // normalized: true,
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
                            },
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
                        position: 'bottom',
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
    await window.engine_health.reload()
})

const EngineHealthLegend = {
    components: {
        LegendItem: LegendItem
    },
    data() {
        return {
            all_selected: true,
            labels: [],
            palette: {}
        }
    },
    async mounted() {
        await this.load_charts()
    },
    watch: {
        all_selected(new_value) {
            this.labels.forEach(i => {
                i.hidden = !new_value
                this.handle_host_visibility_change(i)
            })
            this.update_charts()
        }
    },
    methods: {
        async load_charts() {
            const unique_hosts = new Set()
            Object.values(window.engine_health.charts).forEach(({chart: {data: {hosts}}}) => {
                hosts.forEach(i => unique_hosts.add(i))
                // Chart.defaults.plugins.legend.labels.generateLabels(this.chart_object)
            })
            unique_hosts.forEach(item => {
                const randomHsl = () => `hsl(${Math.random() * 360}, 100%, 60%)`
                let color = this.palette[item]
                if (color === undefined) {
                    color = randomHsl()
                    this.palette[item] = color
                    this.handle_new_color_for_host(item)
                }
                this.labels.push({
                    text: item,
                    hidden: false,
                    datasetIndex: this.labels.length,
                    fillStyle: color
                })
            })
            this.update_charts()
        },
        handle_legend_item_change(item_index) {
            const item = this.labels[item_index]
            item.hidden = !item.hidden

            this.handle_host_visibility_change(item)
            this.update_charts()
        },
        update_charts() {
            Object.values(window.engine_health.charts).forEach(({chart}) => chart.update())
        },
        handle_new_color_for_host(host) {
            Object.values(window.engine_health.charts).forEach(({chart}) => {
                chart.data.datasets.forEach((dataset, index) => {
                    if (dataset.tag_host === host) {
                        dataset.backgroundColor = this.palette[host]
                    }
                })
            })
        },
        handle_host_visibility_change(item) {
            Object.values(window.engine_health.charts).forEach(({chart}) => {
                chart.data.datasets.forEach((dataset, index) => {
                    dataset.tag_host === item.text && chart.setDatasetVisibility(
                        index,
                        !item.hidden
                    )
                })
            })
        },
    },
    template: `
        <div class="d-flex flex-column p-3">
            <label class="mb-0 w-100 d-flex align-items-center custom-checkbox custom-checkbox__multicolor">
                <input class="mx-2 custom__checkbox"
                    type="checkbox"
                    style="--cbx-color: var(--basic);"
                    v-model="all_selected"
                />
                <span class="w-100 d-inline-block">Select/Unselect all</span>
            </label>
        </div>
        <hr class="my-0">
        <div class="custom-chart-legend d-flex flex-column px-3 py-3" style="overflow: scroll; max-height: 450px">
            <LegendItem
                v-for="i in labels"
                :key="i"
                v-bind="i"
                @change="handle_legend_item_change"
            ></LegendItem>
        </div>
        
    `,
}
register_component('EngineHealthLegend', EngineHealthLegend)