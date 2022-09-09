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
                    :checked="!hidden"
                    :style="{'--cbx-color': fillStyle}"
                    @change="$emit('change', this.datasetIndex)"
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
            all_selected: true,
            labels: []
        }
    },
    async mounted() {
        await this.load_chart()
    },
    watch: {
        async chart_object_name(new_value) {
            await this.load_chart()
        },
        all_selected(new_value) {
            this.labels.forEach(i => {
                i.hidden = !new_value
                this.handle_chart_changes(i)
            })
            this.chart_object.update()
        }
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
                :key="i.datasetIndex"
                v-bind="i"
                @change="handle_legend_item_change"
            ></LegendItem>
        </div>
        
    `,
    methods: {
        async load_chart() {
            while (window[this.chart_object_name] === undefined)
                await new Promise(resolve => setTimeout(resolve, 500))
            this.chart_object = window[this.chart_object_name]
            this.labels = Chart.defaults.plugins.legend.labels.generateLabels(this.chart_object)
        },
        handle_legend_item_change(item_index) {
            const item = this.labels[item_index]
            item.hidden = !item.hidden

            this.handle_chart_changes(item)
            this.chart_object.update()
        },
        handle_chart_changes(item) {
            // https://www.chartjs.org/docs/latest/samples/legend/html.html
            const {type} = this.chart_object.config
            if (type === 'pie' || type === 'doughnut') {
                // Pie and doughnut charts only have a single dataset and visibility is per item
                this.chart_object.toggleDataVisibility(item.index)
            } else {
                this.chart_object.setDatasetVisibility(
                    item.datasetIndex,
                    !item.hidden
                    // !this.chart_object.isDatasetVisible(item.datasetIndex)
                )
            }
        }
    },
}

register_component('ChartLegend', ChartLegend)