const LegendItem = {
    delimiters: ['[[', ']]'],
    emits: ['change'],
    props: [
        'text', 'borderRadius', 'datasetIndex', 'fillStyle', 'fontColor', 'hidden', 'lineCap', 'lineDash',
        'lineDashOffset', 'lineJoin', 'lineWidth', 'strokeStyle', 'pointStyle', 'rotation',
        'index'  // for pie/doughnut charts only
    ],
    template: `
        <div class="d-flex mb-3">
            <label class="mb-0 w-100 d-flex align-items-center custom-checkbox custom-checkbox__multicolor">
                <input type="checkbox" class="mx-2 custom__checkbox" 
                    :checked="true"
                    :id="datasetIndex"
                    :style="{'--cbx-color': fillStyle}"
                    @change="$emit('change', this)"
                 />
                 <span class="custom-chart-legend-span"></span>
                 [[ text ]]
             </label>
         </div>
    `,
}

const ChartLegend = {
    components: {
        LegendItem: LegendItem
    },
    props: ['chart_object_name'],
    data() {
        return {
            labels: []
        }
    },
    async mounted() {
        await this.load_chart()
    },
    watch: {
        async chart_object_name(new_value) {
            await this.load_chart()
        }
    },
    template: `
        <LegendItem
            v-for="i in labels"
            v-bind="i"
            :key="i.datasetIndex"
            @change="handle_legend_item_change"
        ></LegendItem>
    `,
    methods: {
        async load_chart() {
            while (window[this.chart_object_name] === undefined)
                await new Promise(resolve => setTimeout(resolve, 500))
            this.chart_object = window[this.chart_object_name]
            this.labels = Chart.defaults.plugins.legend.labels.generateLabels(this.chart_object)
        },
        handle_legend_item_change(item) {
            // https://www.chartjs.org/docs/latest/samples/legend/html.html
            const {type} = this.chart_object.config
            if (type === 'pie' || type === 'doughnut') {
                // Pie and doughnut charts only have a single dataset and visibility is per item
                this.chart_object.toggleDataVisibility(item.index)
            } else {
                this.chart_object.setDatasetVisibility(
                    item.datasetIndex,
                    !this.chart_object.isDatasetVisible(item.datasetIndex)
                )
            }
            this.chart_object.update()
        }
    },
}

register_component('ChartLegend', ChartLegend)