const AnalyticFilter = {
    components: {
        'analytic-filter-block': AnalyticFilterBlock,
    },
    props: ['analyticsData', 'instance_name'],
    data() {
        return {
            blocks: [this.generateBlockId()],
        }
    },
    mounted() {
        $('#analytic-chart-loader').hide();
        $('#chart-analytics').hide();
    },
    methods: {
        addBlock() {
            this.blocks.push(this.generateBlockId())
        },
        removeBlock(blockId) {
            this.blocks = this.blocks.filter(block => block !== blockId);
            const blockLabels = filtersBlock.get(blockId);
            if (blockLabels === undefined) return;
            blockLabels.forEach(blockLabel => {
                let removingIdx = null;
                for (let i in analyticLabels) {
                    if (analyticLabels[i] === blockLabel) {
                        removingIdx = i;
                        break;
                    }
                }
                if (removingIdx) analyticLabels.splice(removingIdx, 1);
            })
            analyticsLine.data.datasets = analyticsLine.data.datasets
                .filter(item => {
                    return analyticLabels.includes(item.label);
                })
            this.switchCartGrid();
            filtersArgsForRequest.delete(blockId);
            filtersBlock.delete(blockId);
            analyticsLine.update();
        },
        switchCartGrid() {
            const hasTimeAxis = analyticsLine.data.datasets.some(ds => ds.yAxisID === "time");
            const hasCountAxis = analyticsLine.data.datasets.some(ds => ds.yAxisID === "count");

            analyticsLine.options.scales.time.display = hasTimeAxis;
            analyticsLine.options.scales.count.display = hasCountAxis;

            analyticsLine.options.scales.time.grid.drawOnChartArea = hasTimeAxis;
            analyticsLine.options.scales.count.grid.drawOnChartArea = hasCountAxis;
            if (hasTimeAxis && hasCountAxis) {
                analyticsLine.options.scales.time.grid.drawOnChartArea = hasTimeAxis;
                analyticsLine.options.scales.count.grid.drawOnChartArea = !hasTimeAxis;
            }
        },
        generateBlockId() {
            return 'blockId_'+Math.round(Math.random() * 1000);
        },
        clearFilter() {
            this.blocks = [this.generateBlockId()];
            clearAnalyticChart();
            filtersBlock = new Map();
            filtersArgsForRequest = new Map();
            analyticLabels = [];
        },
        reDrawChart() {
            if (filtersArgsForRequest.size === 0) return;
            analyticsCanvas(analyticsLine.data);
            this.switchCartGrid();
            analyticsLine.update();
        },
        recalculateChartBySlider() {
            const allRequests = [];
            if (filtersArgsForRequest.size === 0) return;
            filtersArgsForRequest.forEach((filterBlock, blockId, map) => {
                const blockPairs = map.get(blockId);
                blockPairs.forEach((transactions, metric, map) => {
                    const closureRequest = getDataForAnalysis(metric, [...transactions])
                    allRequests.push(closureRequest);
                });
            })
            this.fetchChartDataForAllBlocks(allRequests);
        },
        fetchChartDataForAllBlocks(allRequests) {
            $('#analytic-chart-loader').show();
            Promise.all(allRequests).then(data => {
                analyticsLine.destroy();
                const ds = {
                    labels: data[0].labels,
                    datasets: data.map(ds => ds.datasets).flat().filter(ds => !!ds)
                };
                analyticsCanvas(ds);
                this.switchCartGrid();
                analyticsLine.update();
                $('#analytic-chart-loader').hide();
            }).catch(error => {
                console.log('ERROR', error)
            })
        },
    },
    template: `
        <div id="dataFilter" class="card" style=" width:280px; height: 450px; margin-left: 28px">
            <div class="d-flex justify-content-between align-items-center">
                <p class="font-h5 font-bold py-3 px-4 text-gray-800">DATA FILTER</p>
                <p class="text-purple font-semibold font-h5 cursor-pointer d-flex align-items-center">
                    <span @click="clearFilter">Clear all</span>
                    <i class="icon__16x16 icon-plus__16-purple mx-3 mb-1" @click="addBlock"></i>
                </p>
            </div>
            <div style="overflow: scroll;">
                <div v-for="(block, index) in blocks" :key="block">
                    <hr class="my-0">
                    <div class="py-3 pl-4 pr-3 d-flex align-items-center">
                        <analytic-filter-block
                            :block-index="block"
                            class="flex-grow-1"
                            @register="$root.register"
                            instance_name="analyticFilterBlock"
                            v-bind:analytics-data='analyticsData'
                        >
                        </analytic-filter-block>
                        <i v-if="blocks.length > 1" class="icon__16x16 icon-minus__16 ml-4 mb-3" @click="removeBlock(block)"></i>
                    </div>
                </div> 
            </div>
        </div>
    `
}

register_component('analytic-filter', AnalyticFilter);