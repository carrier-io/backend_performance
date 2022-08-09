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
    methods: {
        addBlock() {
            this.blocks.push(this.generateBlockId())
            // filtersBlock.set(this.blocks.length++, []);
        },
        removeBlock(blockId, index) {
            this.blocks = this.blocks.filter(block => block !== blockId);
            analyticsLine.data.datasets = analyticsLine.data.datasets
                .filter(item => !filtersBlock.get(index).includes(item.label))

            filtersBlock.delete(index);
            analyticsLine.update();
            document.getElementById('chartjs-custom-legend-analytic').innerHTML = analyticsLine.generateLegend();
        },
        generateBlockId() {
            return 'blockId_'+Math.round(Math.random() * 1000);
        },
        clearFilter() {
            this.blocks = [this.generateBlockId()];
            clearAnalyticChart();
        }
    },
    template: `
        <div id="dataFilter" class="card" style=" width:280px; height: 500px; margin-left: 28px">
            <div class="d-flex justify-content-between align-items-center">
                <p class="font-h5 font-bold py-3 px-4 text-gray-800">DATA FILTER</p>
                <p class="text-purple font-semibold font-h5 cursor-pointer d-flex align-items-center">
                    <span @click="clearFilter">Clear all</span>
                    <i class="icon__16x16 icon-plus__16-purple mx-3 mb-1" @click="addBlock"></i>
                </p>
            </div>
            <div style="overflow: scroll; height: 540px;">
                <div v-for="(block, index) in blocks" :key="block">
                    <hr class="my-0">
                    <div class="py-3 pl-4 pr-3 d-flex align-items-center">
                        <analytic-filter-block
                            :block-index="index"
                            class="flex-grow-1"
                                v-bind:analytics-data='analyticsData'>
                        </analytic-filter-block>
                        <i v-if="blocks.length > 1" class="icon__16x16 icon-minus__16 ml-4 mb-3" @click="removeBlock(block, index)"></i>
                    </div>
                </div> 
            </div>
        </div>
    `
}

register_component('analytic-filter', AnalyticFilter);