const AnalyticFilterBlock = {
    components: {
        'analytic-filter-dropdown': AnalyticFilterDropdown,
    },
    props: ['analyticsData', 'blockIndex'],
    data() {
        return {
            transactionItems: null,
            metricItems: null,
            selectedTransactions: [],
            selectedMetrics: [],
            loaded: false,
        }
    },
    mounted() {
        this.transactionItems = Object.keys(this.analyticsData).filter(item => {
            if (item !== '' && item !== "All") return item
        });
        this.metricItems = Object.keys(this.analyticsData["All"])
        this.loaded = true
    },
    methods: {
        setTransactions(payload) {
            this.selectedTransactions = [ ...payload];
        },
        setMetrics(payload) {
            this.selectedMetrics = [ ...payload];
        },
        handlerSubmit() {
            let blockItems = [];
            this.selectedMetrics.forEach(metric => {
                blockItems.push(...this.selectedTransactions.map(transaction => `${transaction}_${metric}`));
            })
            if(filtersBlock.get(this.blockIndex)) {
                analyticsLine.data.datasets = analyticsLine.data.datasets
                    .filter(item => !filtersBlock.get(this.blockIndex).includes(item.label))
            }
            filtersBlock.set(this.blockIndex, blockItems)
            this.selectedMetrics.forEach(metric => {
                getDataForAnalysis(metric, this.selectedTransactions, this.blockIndex);
            })
        }
    },
    template: `
        <div v-if="loaded">
            <p class="font-h5 font-bold mb-1 text-gray-800">Transactions</p>
            <analytic-filter-dropdown
                @select-items="setTransactions"
                :items-list="transactionItems"
            ></analytic-filter-dropdown>
            <p class="font-h5 font-bold my-1 text-gray-800">Metrics</p>
            <analytic-filter-dropdown
                @select-items="setMetrics"
                :items-list="metricItems"
            ></analytic-filter-dropdown>
            <div class="pt-3">
                <button class="btn btn-secondary" @click="handlerSubmit">Apply</button>
            </div>
        </div>
    `
}

register_component('analytic-filter-block', AnalyticFilterBlock);
