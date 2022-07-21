const test_delete = ids => {
    const url = `/api/v1/backend_performance/tests/${getSelectedProjectId()}?` + $.param({"id[]": ids})
    fetch(url, {
        method: 'DELETE'
    }).then(response => response.ok && vueVm.registered_components.table_tests?.table_action('refresh'))
}

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
                <button type="button" class="btn btn-24 btn-action test_run" 
                        data-toggle="tooltip" data-placement="top" title="Run Test"
                >
                    <i class="fas fa-play"></i>
                </button>
                <button type="button" class="btn btn-24 btn-action test_edit">
                    <i class="fas fa-cog"></i>
                </button>
                <button type="button" class="btn btn-24 btn-action">
                    <i class="fas fa-share-alt"></i>
                </button>
                <button type="button" class="btn btn-24 btn-action test_delete">
                    <i class="fas fa-trash-alt"></i>
                </button>
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
    action_events: {
        "click .test_run": function (e, value, row, index) {
            // apiActions.run(row.id, row.name)
            console.log('test_run', row)
            const component_proxy = vueVm.registered_components.run_modal
            component_proxy.set(row)
        },

        "click .test_edit": function (e, value, row, index) {
            console.log('test_edit', row)
            const component_proxy = vueVm.registered_components.create_modal
            component_proxy.mode = 'update'
            component_proxy.set(row)
        },

        "click .test_delete": function (e, value, row, index) {
            console.log('test_delete', row)
            test_delete(row.id)

        }
    }
}

var report_formatters = {
    reportsStatusFormatter(value, row, index) {
        switch (value.toLowerCase()) {
            case 'error':
                return `<div style="color: var(--red)"><i class="fas fa-exclamation-circle error"></i> ${value}</div>`
            case 'failed':
                return `<div style="color: var(--red)"><i class="fas fa-exclamation-circle error"></i> ${value}</div>`
            case 'success':
                return `<div style="color: var(--green)"><i class="fas fa-exclamation-circle error"></i> ${value}</div>`
            case 'canceled':
                return `<div style="color: var(--gray)"><i class="fas fa-times-circle"></i> ${value}</div>`
            case 'finished':
                return `<div style="color: var(--info)"><i class="fas fa-check-circle"></i> ${value}</div>`
            case 'in progress':
                return `<div style="color: var(--basic)"><i class="fas fa-spinner fa-spin fa-secondary"></i> ${value}</div>`
            case 'post processing':
                return `<div style="color: var(--basic)"><i class="fas fa-spinner fa-spin fa-secondary"></i> ${value}</div>`
            case 'pending...':
                return `<div style="color: var(--basic)"><i class="fas fa-spinner fa-spin fa-secondary"></i> ${value}</div>`
            case 'preparing...':
                return `<div style="color: var(--basic)"><i class="fas fa-spinner fa-spin fa-secondary"></i> ${value}</div>`
            default:
                return value
        }
    },
    createLinkToTest(value, row, index) {
        return `<a class="test form-control-label" href="./results?result_id=${row.id}" role="button">${row.name}</a>`
    }
}

const TestCreateModal = {
    delimiters: ['[[', ']]'],
    props: ['modal_id', 'runners', 'test_params_id', 'source_card_id', 'locations'],
    template: `
<div class="modal modal-base fixed-left fade shadow-sm" tabindex="-1" role="dialog" :id="modal_id">
    <div class="modal-dialog modal-dialog-aside" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <div class="row w-100">
                    <div class="col">
                        <h2>[[ mode === 'create' ? 'Create Backend Tests' : 'Update Backend Test' ]]</h2>
                    </div>
                    <div class="col-xs">
                        <button type="button" class="btn btn-secondary mr-2" data-dismiss="modal" aria-label="Close">
                            Cancel
                        </button>
                        <button type="button" class="btn btn-secondary mr-2" 
                            @click="() => handleCreate(false)"
                            v-if="mode === 'create'"
                        >
                            Save
                        </button>
                        <button type="button" class="btn btn-basic" 
                            @click="() => handleCreate(true)"
                            v-if="mode === 'create'"
                        >
                            Save and start
                        </button>
                        <button type="button" class="btn btn-secondary mr-2" 
                            @click="() => handleUpdate(false)"
                            v-if="mode === 'update'"
                        >
                            Update
                        </button>
                        <button type="button" class="btn btn-basic" 
                            @click="() => handleUpdate(true)"
                            v-if="mode === 'update'"
                        >
                            Update and start
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
                                       :disabled="mode !== 'create'"
                                       v-model='name'
                                       :class="{ 'is-invalid': errors?.name , 'disabled': mode !== 'create'}"
                                   >
                                   <div class="invalid-feedback">[[ get_error_msg('name') ]]</div>
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
                                               <div class="invalid-feedback">[[ get_error_msg('test_type') ]]</div>
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
                                               v-model='env_type'
                                               :class="{ 'is-invalid': errors?.env_type }"
                                               >
                                           <div class="invalid-feedback">[[ get_error_msg('env_type') ]]</div>
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
                                <div class="invalid-feedback">[[ get_error_msg('runner') ]]</div>
                                <label class="mb-0 mt-1 w-100 d-flex align-items-center custom-checkbox"
                                    v-if="is_gatling_selected"
                                    >
                                        <input type="checkbox" class="mr-2"
                                            v-model='compile_tests'
                                            :class="{ 'is-invalid': errors?.compile_tests }"
                                            >
                                        <div class="invalid-feedback">[[ get_error_msg('compile_tests') ]]</div>
                                        <h9> Compile tests for Gatling </h9>
                                    </label>
                            </div>
                        </div>
                        <div class="col">
                            <slot name='sources'></slot>
                            
                            <div class="form-group mt-3">
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
                                           <div class="invalid-feedback">[[ get_error_msg('entrypoint') ]]</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                
                <Locations 
                    v-model:location="location"
                    v-model:parallel_runners="parallel_runners"
                    v-model:cpu="cpu_quota"
                    v-model:memory="memory_quota"
                    
                    modal_id="backend"
                    
                    v-bind="locations"
                    ref="locations"
                ></Locations>
                
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
        return this.initial_state()
    },
    mounted() {
        $(this.$el).on('hide.bs.modal', this.clear)
        $(this.$el).on('show.bs.modal', this.$refs.locations.fetch_locations)
        this.runner = this.default_runner
    },
    computed: {
        default_runner() {
            return this.$props.runners &&
                this.$props.runners[Object.keys(this.$props.runners).reverse()[0]][0].version
                || null
        },
        test_parameters() {
            return ParamsTable.Manager(this.$props.test_params_id)
        },
        source() {
            return SourceCard.Manager(this.$props.source_card_id)
        },
        integrations() {
            try {
                return IntegrationSection.Manager()
            } catch (e) {
                console.warn('No integration section')
                return undefined
            }
        },
        scheduling() {
            try {
                return SchedulingSection.Manager()
            } catch (e) {
                console.warn('No scheduling section')
                return undefined
            }
        },
        is_gatling_selected() {
            return Boolean(
                this.$props.runners.Gatling?.find(i => i.version === this.runner) !== undefined
            )
        }
    },
    watch: {
        errors(newValue,) {
            if (Object.keys(newValue).length > 0) {
                newValue.test_parameters ?
                    this.test_parameters.setError(newValue.test_parameters) :
                    this.test_parameters.clearErrors()
                newValue.source ?
                    this.source.setError(newValue.source) :
                    this.source.clearErrors()
                newValue.integrations ?
                    this.integrations?.setError(newValue.integrations) :
                    this.integrations?.clearErrors()
                newValue.scheduling ?
                    this.scheduling?.setError(newValue.scheduling) :
                    this.scheduling?.clearErrors()
            } else {
                this.test_parameters.clearErrors()
                this.source.clearErrors()
                this.integrations?.clearErrors()
                this.scheduling?.clearErrors()
            }
        },
        is_gatling_selected(newValue) {
            if (!newValue) {this.compile_tests = false}
        }
    },
    methods: {
        get_error_msg(field_name) {
            return this.errors[field_name]?.reduce((acc, item) => {
                return acc === '' ? item.msg : [acc, item.msg].join('; ')
            }, '')
        },
        get_data() {

            const data = {
                common_params: {
                    name: this.name,
                    test_type: this.test_type,
                    env_type: this.env_type,
                    entrypoint: this.entrypoint,
                    runner: this.runner,
                    source: this.source.get(),
                    env_vars: {
                        cpu_quota: this.cpu_quota,
                        memory_quota: this.memory_quota
                    },
                    parallel_runners: this.parallel_runners,
                    cc_env_vars: {}
                },
                test_parameters: this.test_parameters.get(),
                integrations: this.integrations?.get() || [],
                scheduling: this.scheduling?.get() || [],
            }
            let csv_files = {}
            $("#splitCSV .flex-row").slice(1,).each(function (_, item) {
                const file = $(item).find('input[type=text]')
                const header = $(item).find('input[type=checkbox]')
                if (file[0].value) {
                    csv_files[file[0].value] = header[0].checked
                }
            })
            if (Object.keys(csv_files).length > 0) {
                data.common_params.cc_env_vars.csv_files = csv_files
            }
            return data
        },
        handle_advanced_params_icon(e) {
            this.advanced_params_icon = this.$refs.advanced_params.classList.contains('show') ?
                'fas fa-chevron-down' : 'fas fa-chevron-up'
        },
        async handleCreate(run_test = false) {
            this.clearErrors()
            const resp = await fetch(`/api/v1/backend_performance/tests/${getSelectedProjectId()}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({...this.get_data(), run_test})
            })
            if (resp.ok) {
                console.log('data', await resp.json())
                this.hide()
            } else {
                await this.handleError(resp)
            }
        },
        async handleUpdate(run_test = false) {
            this.clearErrors()
            const resp = await fetch(`/api/v1/backend_performance/test/${getSelectedProjectId()}/${this.id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({...this.get_data(), run_test})
            })
            if (resp.ok) {
                console.log('data', await resp.json())
                this.hide()
            } else {
                await this.handleError(resp)
            }
        },
        async handleError(response) {
            try {
                const error_data = await response.json()
                this.errors = error_data?.reduce((acc, item) => {
                    const [errLoc, ...rest] = item.loc
                    item.loc = rest
                    if (acc[errLoc]) {
                        acc[errLoc].push(item)
                    } else {
                        acc[errLoc] = [item]
                    }
                    return acc
                }, {})

            } catch (e) {
                alertCreateTest.add(e, 'danger-overlay')
            }
        },
        initial_state() {
            return {
                id: null,
                test_uid: null,

                name: '',
                test_type: '',
                env_type: '',

                location: 'default',
                parallel_runners: 1,
                cpu_quota: 1,
                memory_quota: 4,

                entrypoint: '',
                runner: this.default_runner,
                env_vars: {},
                customization: {},
                cc_env_vars: {},

                compile_tests: false,
                errors: {},

                advanced_params_icon: 'fas fa-chevron-down',
                mode: 'create',
            }
        },
        set(data) {
            console.log('load', data)
            const {test_parameters, integrations, scheduling, source, env_vars: all_env_vars, ...rest} = data

            const {cpu_quota, memory_quota, ...env_vars} = all_env_vars

            let test_type = ''
            let env_type = ''
            const test_parameters_filtered = test_parameters.filter(item => {
                if (item.name === 'test_type') {
                    test_type = item.default;
                    return false
                }
                if (item.name === 'env_type') {
                    env_type = item.default;
                    return false
                }
                if (item.name === 'test_name') {
                    env_type = item.default;
                    return false
                }
                return true
            })
            // common fields
            Object.assign(this.$data, {...rest, cpu_quota, memory_quota, env_vars, test_type, env_type})

            // special fields
            this.test_parameters.set(test_parameters_filtered)
            this.source.set(source)
            integrations && this.integrations.set(integrations)
            scheduling && this.scheduling.set(scheduling)

            this.show()
        },
        clear() {
            Object.assign(this.$data, this.initial_state())
            this.test_parameters.clear()
            this.source.clear()
            this.integrations.clear()
            this.scheduling.clear()
            $('#backend_parallel').text(this.parallel_runners)
            $('#backend_cpu').text(this.cpu_quota)
            $('#backend_memory').text(this.memory_quota)
        },
        clearErrors() {
            this.errors = {}
        },
        show() {
            $(this.$el).modal('show')
        },
        hide() {
            vueVm.registered_components.table_tests?.table_action('refresh')
            $(this.$el).modal('hide')
            // this.clear() // - happens on close event
        }
    }
}

register_component('TestCreateModal', TestCreateModal)


function addCSVSplit(id, key = "", is_header = "") {
    $(`#${id}`).append(`<div class="d-flex flex-row">
    <div class="flex-fill">
        <input type="text" class="form-control form-control-alternative" placeholder="File Path" value="${key}">
    </div>
    <div class="flex-fill m-auto pl-3">
        <div class="form-check">
          <input class="form-check-input" type="checkbox" value="">
          <label class="form-check-label">Ignore first line</label>
        </div>
    </div>
    <div class="m-auto">
        <button type="button" class="btn btn-32 btn-action" onclick="removeParam(event)"><i class="fas fa-minus"></i></button>
    </div>
</div>`)
}


const TestRunModal = {
    delimiters: ['[[', ']]'],
    props: ['test_params_id'],
    template: `
        <div class="modal modal-base fixed-left fade shadow-sm" tabindex="-1" role="dialog" id="runTestModal">
            <div class="modal-dialog modal-dialog-aside" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="row w-100">
                            <div class="col">
                                <h3 class="ml-4 mt-3 mb-3">Run Backend Test</h3>
                            </div>
                            <div class="col-xs">
                                <button type="button" class="btn btn-secondary mr-2" data-dismiss="modal" aria-label="Close">
                                    Cancel
                                </button>
                                <button type="button" class="btn btn-basic" 
                                    @click="handleRun"
                                >
                                    Run test
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="modal-body">
                        <slot name="test_parameters"></slot>
                        <Locations 
                            v-model:location="location"
                            v-model:parallel_runners="parallel_runners"
                            v-model:cpu="cpu_quota"
                            v-model:memory="memory_quota"
                            
                            ref="locations"
                        ></Locations>
                        <div class="row p-4">
                            <div class="col"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    computed: {
        test_parameters() {
            return ParamsTable.Manager(this.$props.test_params_id)
        },

    },
    mounted() {
        $(this.$el).on('hide.bs.modal', this.clear)
        $(this.$el).on('show.bs.modal', this.$refs.locations.fetch_locations)
    },
    data() {
        return this.initial_state()
    },
    methods: {
        initial_state() {
            return {
                id: null,
                test_uid: null,

                location: 'default',
                parallel_runners: 1,
                cpu_quota: 1,
                memory_quota: 4,

                env_vars: {},
                customization: {},
                cc_env_vars: {},

                compile_tests: false,
                errors: {},
            }
        },
        set(data) {
            console.log('set data called', data)
            const {test_parameters, env_vars: all_env_vars, ...rest} = data

            const {cpu_quota, memory_quota, ...env_vars} = all_env_vars

            // common fields
            Object.assign(this.$data, {...rest, cpu_quota, memory_quota, env_vars,})

            // special fields
            this.test_parameters.set(test_parameters)
            this.show()
        },
        show() {
            $(this.$el).modal('show')
        },
        hide() {
            vueVm.registered_components.table_tests?.table_action('refresh')
            $(this.$el).modal('hide')
            // this.clear() // - happens on close event
        },
        clear() {
            Object.assign(this.$data, this.initial_state())
            this.test_parameters.clear()
        },
        clearErrors() {
            this.errors = {}
        },
        get_data() {
            const test_params = this.test_parameters.get()
            const name = test_params.find(i => i.name === 'test_name')
            const test_type = test_params.find(i => i.name === 'test_type')
            const env_type = test_params.find(i => i.name === 'env_type')
            const data = {
                common_params: {
                    name: name,
                    test_type: test_type,
                    env_type: env_type,
                    env_vars: {
                        cpu_quota: this.cpu_quota,
                        memory_quota: this.memory_quota
                    },
                    parallel_runners: this.parallel_runners
                },
                test_parameters: test_params,
            }
            return data
        },
        async handleRun() {
            this.clearErrors()
            const resp = await fetch(`/api/v1/backend_performance/test/${getSelectedProjectId()}/${this.id}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(this.get_data())
            })
            if (resp.ok) {
                console.log('data', await resp.json())
                this.hide()
            } else {
                await this.handleError(resp)
            }
        },
        async handleError(response) {
            try {
                const error_data = await response.json()
                this.errors = error_data?.reduce((acc, item) => {
                    const [errLoc, ...rest] = item.loc
                    item.loc = rest
                    if (acc[errLoc]) {
                        acc[errLoc].push(item)
                    } else {
                        acc[errLoc] = [item]
                    }
                    return acc
                }, {})

            } catch (e) {
                alertCreateTest.add(e, 'danger-overlay')
            }
        },
    },
    watch: {
        errors(newValue,) {
            if (Object.keys(newValue).length > 0) {
                newValue.test_parameters ?
                    this.test_parameters.setError(newValue.test_parameters) :
                    this.test_parameters.clearErrors()
            } else {
                this.test_parameters.clearErrors()
            }
        }
    },
}
register_component('TestRunModal', TestRunModal)


$(document).on('vue_init', () => {
    $('#delete_tests').on('click', e => {
        const ids_to_delete = $(e.target).closest('.card').find('table.table').bootstrapTable('getSelections').map(
            item => item.id
        ).join(',')
        ids_to_delete && test_delete(ids_to_delete)
    })
})
