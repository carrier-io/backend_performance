const DropdownsAnalytic = {
    components: {
        'dropdown-analytic': DropdownAnalytic,
    },
    props: ['analyticsData', 'instance_name'],
    data() {
        return {
            transactionItems: null,
            metricItems: null,
            loaded: false,
        }
    },
    mounted() {
        this.transactionItems = Object.keys(this.analyticsData).filter(item => {
            if (item !== 'All' && item !== '') return item
        })
        this.metricItems = Object.keys(this.analyticsData["All"])
        this.loaded = true
    },
    methods: {
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
    },
    template: `
        <div v-if="loaded">
            <p class="font-h5 font-bold mb-2 mt-3 text-gray-800">Transactions</p>
            <dropdown-analytic
                @select-items="setTransactions"
                :select-items-list="setMetrics"
            ></dropdown-analytic>

            <p class="font-h5 font-bold mb-2 mt-3 text-gray-800">Metrics</p>
            <dropdown-analytic
                @setTransactions="setTransactions"
                :items-list="metricItems"
            ></dropdown-analytic>
        </div>
    `
}

register_component('dropdowns-analytic', DropdownsAnalytic);
