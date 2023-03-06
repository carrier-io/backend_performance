const AnalyticFilterBlock = {
    components: {
        'analytic-filter-dropdown': AnalyticFilterDropdown,
    },
    props: ['analyticsData', 'blockIndex', 'instance_name'],
    data() {
        return {
            transactionItems: null,
            metricItems: null,
            selectedTransactions: [],
            selectedMetrics: [],
            loaded: false,
            loadingData: false,
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
        clearBlockData(blockLabels) {
            blockLabels.forEach(blockLabel => {
                let removingIdx = null;
                for (let i in analyticLabels) {
                    if (analyticLabels[i] === blockLabel) {
                        removingIdx = i;
                        break;
                    }
                }
                analyticLabels.splice(removingIdx, 1);
            })
            analyticsLine.data.datasets = analyticsLine.data.datasets
                .filter(item => {
                    return analyticLabels.includes(item.label);
                })
        },
        fillCurrentBlock() {
            let blockItems = [];
            this.selectedMetrics.forEach(metric => {
                blockItems.push(...this.selectedTransactions.map(transaction => `${transaction}_${metric}`));
            });
            filtersBlock.set(this.blockIndex, blockItems);
        },
        handlerSubmit() {
            if (!this.selectedTransactions.length || !this.selectedMetrics.length) {
                showNotify('INFO', 'Select filter\`s options.');
                return;
            }
            $('#analytic-chart-loader').show();
            const blockLabels = filtersBlock.get(this.blockIndex);
            if (blockLabels !== undefined) {
                this.clearBlockData(blockLabels);
            }
            this.fillCurrentBlock();
            this.prepareRequest();
        },
        prepareRequest() {
            if (this.selectedMetrics.length && this.selectedTransactions.length) {
                const allRequests = [];
                const requestPairs = new Map();
                this.selectedMetrics.forEach(metric => {
                    requestPairs.set(metric, this.selectedTransactions);
                    const closureRequest = getDataForAnalysis(metric, [...this.selectedTransactions])
                    allRequests.push(closureRequest);
                })
                filtersArgsForRequest.set(this.blockIndex, requestPairs)
                this.fetchChartData(allRequests);
            }
        },
        fetchChartData(allRequests) {
            this.loadingData = true;
            if (!analyticsLine) {
                $('#chart-analytics').show();
                $('#layout_empty-chart').hide();
            }
            Promise.all(allRequests).then(data => {
                data.forEach(chartData => {
                    if (Object.keys(chartData).length === 0) {
                        return;
                    }
                    if (!analyticsLine) {
                        analyticsCanvas(chartData);
                        chartData.datasets.forEach(dataset => {
                            analyticLabels.push(dataset.label);
                        });
                    } else {
                        const uniqueDatasets = chartData.datasets.filter(item => {
                            const isValueNotExist = analyticsLine.data.datasets.some(currentItem => currentItem.label === item.label)
                            if (!isValueNotExist) return item
                        });
                        chartData.datasets.forEach(dataset => {
                                analyticLabels.push(dataset.label);
                        })
                        analyticsLine.data.datasets.push(...uniqueDatasets);
                    }
                    turnOnAllLine();
                })
                this.switchCartGrid();
                analyticsLine.update();
                $('#analytic-chart-loader').hide();
                this.loadingData = false;
            }).catch(error => {
                console.log('ERROR', error)
            })
        },
        switchCartGrid() {
            const hasTimeAxis = analyticsLine.data.datasets.some(ds => ds.yAxisID === "time");
            const hasCountAxis = analyticsLine.data.datasets.some(ds => ds.yAxisID === "count");
            analyticsLine.options.scales.time.display = hasTimeAxis;
            analyticsLine.options.scales.count.display = hasCountAxis;
            if (hasTimeAxis) {
                analyticsLine.options.scales.count.grid.drawOnChartArea = !hasTimeAxis;
                analyticsLine.options.scales.time.grid.drawOnChartArea = hasTimeAxis;
            } else {
                analyticsLine.options.scales.count.grid.drawOnChartArea = hasTimeAxis;
                analyticsLine.options.scales.time.grid.drawOnChartArea = !hasTimeAxis;
            }
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
                <button class="btn btn-secondary"
                    :disabled="loadingData"
                    style="position: relative; padding-right: 24px"
                    @click="handlerSubmit">Apply
                    <i
                        v-if="loadingData"
                        class="spinner-loader" 
                        style="position: absolute; top: 8px; right: 5px"></i>
                </button>
            </div>
        </div>
    `
}

register_component('analytic-filter-block', AnalyticFilterBlock);
