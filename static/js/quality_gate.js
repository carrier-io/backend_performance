const QualityGate = {
    delimiters: ['[[', ']]'],
    props: ['instance_name', 'section', 'selected_integration', 'is_selected'],
    emits: ['set_data', 'clear_data'],
    delimiters: ['[[', ']]'],
    data() {
        return this.initialState()
    },
    methods: {
        get_data() {
            if (this.is_selected) {
                const {
                    SLA, 
                    baseline,
                    request_check,
                    summary_check,
                    summary_check_response_time,
                    summary_check_error_rate,
                    summary_check_throughput,
                    request_check_response_time,
                    request_check_error_rate,
                    request_check_throughput,
                    summary_response_time_deviation,
                    summary_error_rate_deviation,
                    summary_throughput_deviation,
                    request_response_time_deviation,
                    request_error_rate_deviation,
                    request_throughput_deviation,
                    percentage_of_failed_requests,
                    rt_baseline_comparison_mecric,
                } = this
                return {
                    SLA: {
                        checked: SLA
                        },
                    baseline: {
                        checked: baseline,
                        rt_baseline_comparison_mecric: rt_baseline_comparison_mecric
                        },
                    settings: {
                        summary_results: {
                            check_response_time: summary_check && summary_check_response_time,
                            response_time_deviation: summary_response_time_deviation,
                            check_error_rate: summary_check && summary_check_error_rate,
                            error_rate_deviation: summary_error_rate_deviation,
                            check_throughput: summary_check && summary_check_throughput,
                            throughput_deviation: summary_throughput_deviation
                            },
                        per_request_results: {
                            check_response_time: request_check && request_check_response_time,
                            response_time_deviation: request_response_time_deviation,
                            check_error_rate: request_check && request_check_error_rate,
                            error_rate_deviation: request_error_rate_deviation,
                            check_throughput: request_check && request_check_throughput,
                            throughput_deviation: request_throughput_deviation,
                            percentage_of_failed_requests: percentage_of_failed_requests
                            }
                        }
                    }
            }
        },
        set_data(data) {
            const {id, ...rest} = data
            this.load(rest)
            this.$emit('set_data', {id: 'quality_gate'})
        },
        clear_data() {
            Object.assign(this.$data, this.initialState())
            this.$emit('clear_data')
        },
        load(data) {
            data_to_load = {
                SLA: data.SLA.checked,
                baseline: data.baseline.checked,
                request_check: data.settings.per_request_results.check_response_time || 
                               data.settings.per_request_results.check_error_rate || 
                               data.settings.per_request_results.check_throughput,
                summary_check: data.settings.summary_results.check_response_time || 
                               data.settings.summary_results.check_error_rate || 
                               data.settings.summary_results.check_throughput,
                summary_check_response_time: data.settings.summary_results.check_response_time,
                summary_check_error_rate: data.settings.summary_results.check_error_rate,
                summary_check_throughput: data.settings.summary_results.check_throughput,
                request_check_response_time: data.settings.per_request_results.check_response_time,
                request_check_error_rate: data.settings.per_request_results.check_error_rate,
                request_check_throughput: data.settings.per_request_results.check_throughput,
                summary_response_time_deviation: data.settings.summary_results.response_time_deviation,
                summary_error_rate_deviation: data.settings.summary_results.error_rate_deviation,
                summary_throughput_deviation: data.settings.summary_results.throughput_deviation,
                request_response_time_deviation: data.settings.per_request_results.response_time_deviation,
                request_error_rate_deviation: data.settings.per_request_results.error_rate_deviation,
                request_throughput_deviation: data.settings.per_request_results.throughput_deviation,
                percentage_of_failed_requests: data.settings.per_request_results.percentage_of_failed_requests,
                rt_baseline_comparison_mecric: data.baseline.rt_baseline_comparison_mecric
            }
            Object.assign(this.$data, {...this.initialState(), ...data_to_load})
        },
        set_error(data) {
            this.errors[`${data.loc[data.loc.length - 2]}_${data.loc[data.loc.length - 1]}`] = data.msg
            console.log(this.errors)
        },
        clear_errors() {
            this.errors = {}
        },
        initialState: () => ({
            SLA: false,
            baseline: false,
            request_check: false,
            summary_check: false,
            summary_check_response_time: true,
            summary_check_error_rate: true,
            summary_check_throughput: true,
            request_check_response_time: true,
            request_check_error_rate: true,
            request_check_throughput: true,
            summary_response_time_deviation: 100,
            summary_error_rate_deviation: 1,
            summary_throughput_deviation: 1,
            request_response_time_deviation: 100,
            request_error_rate_deviation: 1,
            request_throughput_deviation: 1,
            percentage_of_failed_requests: 20,
            rt_baseline_comparison_mecric: "pct95",
            is_adv_settins_open: false,
            errors: {},

        })
    },
    template: `
    <div class="mb-2 d-flex">
        <label class="mb-0 mt-1 w-100 d-flex align-items-center custom-checkbox">
            <input type="checkbox"
                v-model="SLA"
            >
            <p class="font-h5 ml-2">SLA</p>
        </label>
    </div>
    <div class="mb-2 d-flex">
        <label class="mb-0 mt-1 w-100 d-flex align-items-center custom-checkbox">
            <input type="checkbox"
                v-model="baseline"
            >
            <p class="font-h5 ml-2">Baseline</p>
        </label>
    </div>

    <div class="mt-3">
        <div class="row" 
                data-toggle="collapse" 
                data-target="#selector_advanced_settings" 
                role="button" 
                aria-expanded="false" 
                aria-controls="selector_advanced_settings"
                @click="is_adv_settins_open = !is_adv_settins_open"
            >
            <div>
                <p class="font-h6 font-semibold text-gray-600">ADVANCED SETTINGS 
                    <button class="btn btn-nooutline-secondary p-0 pb-1 ml-1 collapsed">
                        <i class="icon__16x16 icon-arrow-down__16" :class="is_adv_settins_open ? '' : 'rotate-270'"></i>
                    </button>
                </p>
            </div>
            <div class="col">
                <div class="col-xs text-right">
                    <button type="button" class="btn btn-nooutline-secondary mr-2"
                            data-toggle="collapse" data-target="#selector_advanced_settings">
                    </button>
                </div>
            </div>
        </div>

        <div class="collapse" id="selector_advanced_settings">
            <div class="d-grid grid-column-2 gap-4">
                <div>
                    <div class="mt-4 mb-4 d-flex">
                        <p class="font-h5 font-semibold flex-grow-1">Summary results</p>
                        <label class="custom-toggle">
                            <input type="checkbox"
                                v-model="summary_check"
                                data-target="#selector_summary_check"
                                aria-expanded="summary_check"
                                data-toggle="collapse"
                            >
                            <span class="custom-toggle_slider round"></span>
                        </label>
                    </div> 
                    <div class="mb-2 collapse" :class="{ show: summary_check }" id="selector_summary_check">
                        <div class="row">
                            <div class="col-7 mb-2 d-flex">
                                <label class="mt-1 d-flex align-items-center custom-checkbox">
                                    <input type="checkbox"
                                        v-model="summary_check_response_time"
                                    >
                                    <p class="font-h5 ml-2">Check response time</p>
                                </label>
                            </div>
                            <div class="col mb-2 align-items-center">
                                <div class="font-h6 font-semibold" style="white-space: nowrap">deviation = </div>
                                <input type="number" class="form-control mt-1" placeholder="Response time deviation"
                                    v-model="summary_response_time_deviation"
                                    :class="{ 'is-invalid': errors.summary_results_response_time_deviation }"
                                >
                                <div class="invalid-feedback">[[ errors.summary_results_response_time_deviation ]]</div>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-7 mb-2 d-flex">
                                <label class="mt-1 d-flex align-items-center custom-checkbox">
                                    <input type="checkbox"
                                        v-model="summary_check_error_rate"
                                    >
                                    <p class="font-h5 ml-2">Check error rate</p>
                                </label>
                            </div>
                            <div class="col mb-2 align-items-center">
                                <div class="font-h6 font-semibold" style="white-space: nowrap">deviation = </div>
                                <input type="number" class="form-control mt-1" placeholder="Error rate deviation"
                                    v-model="summary_error_rate_deviation"
                                    :class="{ 'is-invalid': errors.summary_results_error_rate_deviation }"
                                >
                                <div class="invalid-feedback">[[ errors.summary_results_error_rate_deviation ]]</div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-7 mb-2 d-flex">
                                <label class="mt-1 d-flex align-items-center custom-checkbox">
                                    <input type="checkbox"
                                        v-model="summary_check_throughput"
                                    >
                                    <p class="font-h5 ml-2">Check throughput</p>
                                </label>
                            </div>
                            <div class="col mb-2 align-items-center">
                                <div class="font-h6 font-semibold" style="white-space: nowrap">deviation = </div>
                                <input type="number" class="form-control mt-1" placeholder="Throughput deviation"
                                    v-model="summary_throughput_deviation"
                                    :class="{ 'is-invalid': errors.summary_results_throughput_deviation }"
                                >
                                <div class="invalid-feedback">[[ errors.summary_results_throughput_deviation ]]</div>
                            </div>
                        </div>
                    </div>
                </div> 
                
                <div>
                    <div class="mt-4 mb-4 d-flex">
                        <p class="font-h5 font-semibold flex-grow-1">Per request results</p>
                        <label class="custom-toggle">
                            <input type="checkbox"
                                v-model="request_check"
                                data-target="#selector_request_check" 
                                :aria-expanded="request_check"
                                data-toggle="collapse"
                            >
                            <span class="custom-toggle_slider round"></span>
                        </label>
                    </div> 
                    <div class="mb-2 collapse" :class="{ show: request_check }" id="selector_request_check">
                        <div class="row">
                            <div class="col-7 mb-2 d-flex">
                                <label class="mt-1 d-flex align-items-center custom-checkbox">
                                    <input type="checkbox"
                                        v-model="request_check_response_time"
                                    >
                                    <p class="font-h5 ml-2">Check response time</p>
                                </label>
                            </div>
                            <div class="col mb-2 align-items-center">
                                <div class="font-h6 font-semibold" style="white-space: nowrap">deviation = </div>
                                <input type="number" class="form-control mt-1" placeholder="Response time deviation"
                                    v-model="request_response_time_deviation"
                                    :class="{ 'is-invalid': errors.per_request_results_response_time_deviation }"
                                >
                                <div class="invalid-feedback">[[ errors.per_request_results_response_time_deviation ]]</div>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-7 mb-2 d-flex">
                                <label class="mt-1 d-flex align-items-center custom-checkbox">
                                    <input type="checkbox"
                                        v-model="request_check_error_rate"
                                    >
                                    <p class="font-h5 ml-2">Check error rate</p>
                                </label>
                            </div>
                            <div class="col mb-2 align-items-center">
                                <div class="font-h6 font-semibold" style="white-space: nowrap">deviation = </div>
                                <input type="number" class="form-control mt-1" placeholder="Error rate deviation"
                                    v-model="request_error_rate_deviation"
                                    :class="{ 'is-invalid': errors.per_request_results_error_rate_deviation }"
                                >
                                <div class="invalid-feedback">[[ errors.per_request_results_error_rate_deviation ]]</div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-7 mb-2 d-flex">
                                <label class="mt-1 d-flex align-items-center custom-checkbox">
                                    <input type="checkbox"
                                        v-model="request_check_throughput"
                                    >
                                    <p class="font-h5 ml-2">Check throughput</p>
                                </label>
                            </div>
                            <div class="col mb-2 align-items-center">
                                <div class="font-h6 font-semibold" style="white-space: nowrap">deviation = </div>
                                <input type="number" class="form-control mt-1" placeholder="Throughput deviation"
                                    v-model="request_throughput_deviation"
                                    :class="{ 'is-invalid': errors.per_request_results_throughput_deviation }"
                                >
                                <div class="invalid-feedback">[[ errors.per_request_results_throughput_deviation ]]</div>
                            </div>
                        </div>

                        <div class="row align-items-center">
                            <div class="font-h5 col-7 mb-2">Percentage of failed requests</div>
                            <div class="col mb-2">
                                <input type="number" class="form-control mt-1" placeholder="Failed requests"
                                    v-model="percentage_of_failed_requests"
                                    :class="{ 'is-invalid': errors.per_request_results_percentage_of_failed_requests }"
                                >
                                <div class="invalid-feedback">[[ errors.per_request_results_percentage_of_failed_requests ]]</div>
                            </div>
                        </div>

                        <div class="row align-items-center">
                            <div class="col-7 mb-2">
                                <div class="font-h5">Comparison metric</div>
                                <p>
                                <h13>Math aggregation to be applied for baseline calculation.</h13>
                                </p>
                            </div>
                            <div class="col mb-2 d-flex flex-column w-100">
                                <select class="selectpicker bootstrap-select__b" data-style="btn"
                                    v-model="rt_baseline_comparison_mecric">
                                    <option value="max">Maximum</option>
                                    <option value="min">Minimum</option>
                                    <option value="avg">Average</option>
                                    <option value="pct95">Percentile 95</option>
                                    <option value="pct50">Percentile 50</option>
                                </select>
                                <div class="invalid-feedback" style="display: block;">[[ errors.baseline_rt_baseline_comparison_mecric ]]</div>
                            </div>
                        </div>


                    </div>
                </div> 
            </div>
        </div>
    </div>
    `,
}

register_component('quality-gate', QualityGate)
