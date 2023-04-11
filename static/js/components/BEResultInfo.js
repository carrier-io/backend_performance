const BEResultInfo = {
    props: ['test_data', 'instance_name'],
    components: {
        'BEResultTagsModal': BEResultTagsModal
    },
    data() {
        return {
            existedTags: [],
            servicesTags: [],
            isLoading: false,
            isDataLoaded: false,
            isUpdatedTags: false,
        }
    },
    computed: {
        buttonsTag() {
            return this.existedTags.filter(tag => tag.selected)
        },
    },
    mounted() {
        this.fetchTags();
    },
    methods: {
        fetchTags() {
            this.isUpdatedTags = false;
            this.fetchTagsAPI().then(({ tags }) => {
                this.existedTags = tags.map(tag => {
                    const obj = {
                        title: tag.title,
                        hex: tag.hex,
                    }
                    if (tag.is_selected) {
                        obj.selected = 'selected'
                    }
                    return obj;

                });
                this.fetchServiceTagsAPI().then(res => {
                    this.servicesTags = res['service tags'];
                    this.isDataLoaded = true;
                })
            })
        },
        updateTags(selectedTags) {
            this.updateTagsAPI(selectedTags)
        },
        async fetchTagsAPI () {
            const res = await fetch(`/api/v1/backend_performance/tags/${getSelectedProjectId()}?report_id[]=${this.test_data.id}`, {
                method: 'GET',
            })
            return res.json();
        },
        async fetchServiceTagsAPI () {
            const res = await fetch(`/api/v1/backend_performance/tags/${getSelectedProjectId()}`, {
                method: 'GET',
            })
            return res.json();
        },
        updateTagsAPI(newTags) {
            this.isLoading = true;
            fetch(`/api/v1/backend_performance/tags/${getSelectedProjectId()}/${this.test_data.id}`, {
                method: 'POST',
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ tags: newTags })
            }).then(() => {
                this.isLoading = false;
                $('#exampleModal').modal('hide');
                this.isUpdatedTags = true;
                this.isDataLoaded = false;
                this.$nextTick(() => {
                    this.fetchTags();
                })
            })
        }
    },
    template: `
        <div class="mt-24">
            <div class="d-grid grid-column-5 gap-3">
                <div class="">
                    <div class="card card-sm card-blue">
                        <div class="card-header">{{ test_data["vusers"] }} VU</div>
                        <div class="card-body">MAX VUSERS</div>
                    </div>
                </div>
                <div class="">
                    <div class="card card-sm card-blue">
                        <div class="card-header">{{ test_data["throughput"] }} req/sec</div>
                        <div class="card-body">AVG.THROUGHPUT</div>
                    </div>
                </div>
                <div class="">
                    <div class="card card-sm card-blue">
                        <div class="card-header">{{ test_data["failure_rate"] }} %</div>
                        <div class="card-body">ERROR RATE</div>
                    </div>
                </div>
                <div class="">
                    <div class="card card-sm card-blue">
                        <div class="card-header">{{ test_data["pct95"] }} ms</div>
                        <div class="card-body">95 PCT. RESP. TIME</div>
                    </div>
                </div>
                <div class="">
                    <div class="card card-sm card-blue">
                        <div class="card-header">{{ test_data["pct50"] }} ms</div>
                        <div class="card-body">MEDIAN RESP. TIME</div>
                    </div>
                </div>
            </div>
            <div id="processing-table" class="d-grid grid-column-2 mt-24">
                <div class="d-flex justify-content-between">
                    <table class="table-card-result">
                        <tr>
                            <td class="font-h6 text-gray-500 font-semibold font-uppercase pr-3">Status</td>
                            <td class="font-h5">{{ test_data['test_status']['status'] }}</td>
                        </tr>
                        <tr>
                            <td class="text-gray-500 font-h6 font-semibold font-uppercase pr-3">DURATION</td>
                            <td class="font-h5">{{ test_data["duration"] }} s</td>
                        </tr>
                    </table>
                    <table>
                        <tr>
                            <td class="text-gray-500 font-h6 font-semibold font-uppercase pr-3">STARTED</td>
                            <td class="font-h5" id="start_time">{{ test_data["start_time"] }}</td>
                        </tr>
                        <tr>
                            <td class="text-gray-500 font-h6 font-semibold font-uppercase pr-3">ENDED</td>
                            <td class="font-h5" id="end_time">{{ test_data["end_time"] }}</td>
                        </tr>
                    </table>
                    <table>
                        <tr>
                            <td class="text-gray-500 font-h6 font-semibold font-uppercase pr-3">TEST TYPE</td>
                            <td class="font-h5">{{ test_data["type"] }}</td>
                        </tr>
                        <tr>
                            <td class="text-gray-500 font-h6 font-semibold font-uppercase pr-3">Environment</td>
                            <td class="font-h5">{{ test_data["environment"] }}</td>
                        </tr>
                    </table>
                </div>
                <div class="d-flex justify-content-center">
                    <table>
                        <tr>
                            <td class="text-gray-500 font-h6 font-semibold pr-3">RESPONSE CODES</td>
                            <td>
                                <p class="font-h5 text-gray-500">
                                    1xx: <span class="compact-format text-gray-600 mx-1">{{ test_data["onexx"] }}</span>
                                    2xx: <span class="compact-format text-gray-600 mx-1">{{ test_data["twoxx"] }}</span>
                                    3xx: <span class="compact-format text-gray-600 mx-1">{{ test_data["threexx"] }}</span>
                                    4xx: <span class="compact-format text-gray-600 mx-1">{{ test_data["fourxx"] }}</span>
                                    5xx: <span class="compact-format text-gray-600 mx-1">{{ test_data["fivexx"] }}</span>
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td class="text-gray-500 font-h6 font-semibold pr-3">TAGS</td>
                            <td> 
                                <div class="d-flex flex-wrap gap-1" style="max-width: 258px">
                                    <button v-for="tag in buttonsTag" class="btn btn-xs btn-painted rounded-pill"
                                        :style="{ '--text-color': tag.hex, '--brd-color': tag.hex }">{{ tag.title }}
                                    </button>
                                    <button type="button" class="btn btn-default btn-xs btn-icon__xs mr-2"
                                        data-toggle="modal" data-target="#exampleModal">
                                        <i class="icon__18x18 icon-edit" data-toggle="tooltip" data-placement="top" title="Edit tags"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>
            </div>
            <div hidden class="row">
                <div class="col-12 d-flex align-items-center mt-4" id="dropdowns">
                    <p class="mb-0 font-h6 text-gray-500 font-semibold">LOAD CONFIG</p>
                    <multiselect-filter :title="'Carrier default'">
                    </multiselect-filter>
                    <multiselect-filter :title="'Custom location'">
                    </multiselect-filter>
                </div>
            </div>
            <BEResultTagsModal
                :existed-tags="existedTags"
                :services-tags="servicesTags"
                :is-loading="isLoading"
                :is-data-loaded="isDataLoaded"
                :key="isUpdatedTags"
                @update-tags="updateTags"
                >  
            </BEResultTagsModal>
        </div>
    `
}

register_component('BEResultInfo', BEResultInfo);