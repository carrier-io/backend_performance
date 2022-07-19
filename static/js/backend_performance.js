var test_formatters = {
    job_type(value, row, index) {
        if (row.job_type === "perfmeter") {
            return '<img src="/design-system/static/assets/ico/jmeter.png" width="20">'
        } else if (row.job_type === "perfgun") {
            return '<img src="/design-system/static/assets/ico/gatling.png" width="20">'
        } else {
            return value
        }
    },
    actions(value, row, index) {
        return `
            <div class="d-flex justify-content-end">
                <button type="button" class="btn btn-24 btn-action" onclick="runTestModal('${row.id}')" data-toggle="tooltip" data-placement="top" title="Run Test"><i class="fas fa-play"></i></button>
                <button type="button" class="btn btn-24 btn-action" onclick="editTest('${row.id}')"><i class="fas fa-cog"></i></button>
                <button type="button" class="btn btn-24 btn-action"><i class="fas fa-share-alt"></i></button>
                <button type="button" class="btn btn-24 btn-action" onclick="deleteTests('${row.id}')"><i class="fas fa-trash-alt"></i></button>
            </div>
        `
    },
    name_style(value, row, index) {
        return {
            css: {
                "max-width": "140px",
                "overflow": "hidden",
                "text-overflow": "ellipsis",
                "white-space": "nowrap"
            }
        }
    },
    cell_style(value, row, index) {
        return {
            css: {
                "min-width": "165px"
            }
        }
    },

}

const TestCreateModal = {
    delimiters: ['[[', ']]'],
    props: ['modal_id', 'modal_header', 'runners', 'test_params_id'],
    template: `
<div class="modal modal-base fixed-left fade shadow-sm" tabindex="-1" role="dialog" :id="modal_id">
    <div class="modal-dialog modal-dialog-aside" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <div class="row w-100">
                    <div class="col">
                        <h2>[[ modal_header ]]</h2>
                    </div>
                    <div class="col-xs">
                        <button type="button" class="btn btn-secondary mr-2" data-dismiss="modal" aria-label="Close">
                            Cancel
                        </button>
                        <button type="button" id="submit" class="btn btn-secondary mr-2" 
                            @click="handleCreate"
                        >
                            Save
                        </button>
                        <button type="button" id="save" class="btn btn-basic" 
                            @click="() => handleCreate(true)"
                        >
                            Save and start
                        </button>
                    </div>
                </div>
            </div>
            
            <slot name='alert_bar'></slot>


            <div class="modal-body">
                <div class="section">
                    <div class="row">
                        <div class="col">
                            <div class="form-group">
                                <h9>Test Name</h9>
                                <p>
                                    <h13>Enter a name that describes the purpose of your test.</h13>
                                </p>
                                <input type="text" class="form-control form-control-alternative"
                                       placeholder="Test Name"
                                       v-model='name'
                                       :class="{ 'is-invalid': errors?.name }"
                                   >
                                   <div class="invalid-feedback">[[ errors.name ]]</div>
                            </div>
                            <div class="d-flex">
                                <div class="flex-fill">
                                    <div class="form-group">
                                        <h9>Test Type</h9>
                                        <p>
                                            <h13>Tag to group tests by type</h13>
                                        </p>
                                        <input type="text" class="form-control form-control-alternative"
                                               placeholder="Test Type"
                                               v-model='test_type'
                                               :class="{ 'is-invalid': errors?.test_type }"
                                               >
                                               <div class="invalid-feedback">[[ errors.test_type ]]</div>
                                    </div>
                                </div>
                                <div class="flex-fill">
                                    <div class="form-group">
                                        <h9>Environment</h9>
                                        <p>
                                            <h13>Tag to group tests by env</h13>
                                        </p>
                                        <input type="text" class="form-control form-control-alternative"
                                               placeholder="Test Environment"
                                               v-model='test_env'
                                               :class="{ 'is-invalid': errors?.test_env }"
                                               >
                                           <div class="invalid-feedback">[[ errors.test_env ]]</div>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group" >
                                <h9>Test runner</h9>
                                <p>
                                    <h13>Choose the runner for the test.</h13>
                                </p>
                                <select class="selectpicker bootstrap-select__b mt-1" data-style="btn" 
                                v-model="runner"
                                :class="{ 'is-invalid': errors?.runner }"
                                >
                                    
                                    <optgroup v-for='runner_group in Object.keys(runners).reverse()' :label="runner_group">
                                        <option v-for='runner in runners[runner_group]' :value="runner.version">
                                            [[ runner.name || runner_group + " " + runner.version ]]
                                        </option>
                                    </optgroup>
                                </select>
                                <div class="invalid-feedback">[[ errors.runner ]]</div>
                            </div>
                            <div class="form-group">
                                <div class="custom-control custom-checkbox custom-control-inline">
                                    <label class="custom-control-label" for="compile">
                                    Compile tests for Gatling
                                    <input type="checkbox" class="custom-control-input" disabled 
                                        v-model='compile_tests'
                                        :class="{ 'is-invalid': errors?.compile_tests }"
                                        >
                                        <div class="invalid-feedback">[[ errors.compile_tests ]]</div>
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="col">
                            <slot name='sources'></slot>
                            
                            <div class="form-group mt-2">
                                <div class="form-group">
                                    <h9>Entrypoint</h9>
                                    <p>
                                        <h13>File for jMeter and class for gatling</h13>
                                    </p>
                                    <input type="text" class="form-control form-control-alternative"
                                           placeholder="Entrypoint (e.g. some.jmx or some.Test)"
                                           v-model='entrypoint'
                                           :class="{ 'is-invalid': errors?.entrypoint }"
                                           >
                                           <div class="invalid-feedback">[[ errors.entrypoint ]]</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                
                <slot name='locations'></slot>
                <slot name='params_table'></slot>
                <slot name='integrations'></slot>
                <slot name='scheduling'></slot>
                

                <div class="section mt-3" @click="handle_advanced_params_icon">
                    <div class="row" data-toggle="collapse" data-target="#advancedBackend" role="button" aria-expanded="false" aria-controls="advancedBackend">
                        <div class="col">
                            <h7>ADVANCED PARAMETERS</h7>
                            <p>
                                <h13>Configure parameters for test runner, test data and network setting</h13>
                            </p>
                        </div>
                        <div class="col">
                            <div class="col-xs text-right">
                                <button type="button" class="btn btn-nooutline-secondary mr-2"
                                        data-toggle="collapse" data-target="#advancedBackend">
                                        <i :class="advanced_params_icon"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="collapse row pt-4" id="advancedBackend"
                        ref="advanced_params"
                    >
                        <div class="col">
                            <div class="card card-x card-row-1">
                                <div class="card-header">
                                    <div class="d-flex flex-row">
                                        <div class="flex-fill">
                                            <h9 class="flex-grow-1">Custom plugins and extensions</h9>
                                            <p>
                                                <h13>Bucket and file for your customizations</h13>
                                            </p>
                                        </div>
                                        <div>
                                            <button type="button" class="btn btn-32 btn-action mt-1"
                                                    onclick="addParam('extCard', 'bucket/file', 'path/to/file')"><i
                                                    class="fas fa-plus"></i></button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="card card-x card-row-1" id="splitCSV">
                                <div class="card-header">
                                    <div class="d-flex flex-row">
                                        <div class="flex-fill">
                                            <h9 class="flex-grow-1">Split CSV</h9>
                                            <p>
                                                <h13>Distribute CSV data across load generators</h13>
                                            </p>
                                        </div>
                                        <div>
                                            <button type="button" class="btn btn-32 btn-action mt-1"
                                                    onclick="addCSVSplit('splitCSV')"><i class="fas fa-plus"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col">
                            <div class="card card-x card-row-1" id="dnsCard">
                                <div class="card-header">
                                    <div class="d-flex flex-row">
                                        <div class="flex-fill">
                                            <h9 class="flex-grow-1">DNS Override</h9>
                                            <p>
                                                <h13>Specify alternative IPs for hosts used in your script</h13>
                                            </p>
                                        </div>
                                        <div>
                                            <button type="button" class="btn btn-32 btn-action mt-1"
                                                    onclick="addParam('dnsCard', 'hostname.company.com', '0.0.0.0')"><i
                                                    class="fas fa-plus"></i></button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
    `,
    data() {
        return {
            name: '',
            test_type: '',
            test_env: '',
            compile_tests: false,
            entrypoint: '',
            runner: null,
            errors: {},
            advanced_params_icon: 'fas fa-chevron-down'
        }
    },
    mounted() {
        this.runner = this.default_runner
    },
    computed: {
        // advanced_params_icon() {
        //     console.log('advanced_params_icon', this.$refs.advanced_params)
        //     return 'fas fa-chevron-down'
        // }
        // runners_ordered() {
        //     return Object.keys(this.$props.runners).sort((a, b) => a.toLowerCase() === 'jmeter' ? 1 : 0)
        // }
        default_runner() {
            return this.$props.runners &&
                this.$props.runners[Object.keys(this.$props.runners).reverse()[0]][0].version
                || null
        },
        test_parameters() {
            console.log('COMPUTED')
            return ParamsTable.Manager(this.$props.test_params_id)
        },
        body_data() {
            const data = {
                common_params: {
                    name: this.name,
                    entrypoint: this.entrypoint,
                    runner: this.runner,
                },
                test_parameters: this.test_parameters.get()
            }
            if (vueVm.scheduling) { data['scheduling'] = vueVm.scheduling }
            return data
        }

    },
    methods: {
        handle_advanced_params_icon(e) {
            this.advanced_params_icon = this.$refs.advanced_params.classList.contains('show') ?
                'fas fa-chevron-down' : 'fas fa-chevron-up'
        },
        handleClose() {
            $(this.$el).modal('hide')
        },
        async handleCreate(run_test = false) {
            const resp = await fetch(`/api/v2/backend_performance/tests/${getSelectedProjectId()}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({...this.body_data, run_test})
            })
            if (resp.ok) {
                console.log('data', data)
                this.handleClose()
            } else {
                await this.handleError(resp)
            }
        },
        async handleError(response) {
            try {
                const error_data = await response.json()
                error_data.forEach(item => {
                    this.errors[item.loc[0]] = item.msg
                })
            } catch (e) {
                alertMain.add(e, 'danger-overlay')
            }
        },
    }
}

register_component('TestCreateModal', TestCreateModal)
