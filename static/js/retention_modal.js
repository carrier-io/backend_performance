const RetentionModal = {
    delimiters: ['[[', ']]'],
    props: ['modal_id', 'result_uid'],
    data() {
        return {
            initial_retention: undefined,
            time_type: undefined,
            time_amount: 1,
            ttl: undefined,
            ts: undefined,
            default_retention: undefined
        }
    },
    mounted() {
        $(this.$el).on('show.bs.modal', () => {
            if (this.initial_retention === undefined) {
                $(document).ready(this.fetch_retention)
            }
        })
    },
    watch: {
        time_type(newValue) {
            this.$nextTick(this.refresh_pickers)
        },
        initial_retention(newValue) {
            Object.assign(this.$data, this.process_retention(newValue))
        }
    },
    computed: {
        remaining_time() {
            if (this.initial_retention === null) {
                return 'Never'
            }
            const delta = new Date(this.ttl) - new Date()
            if (delta < 0) {
                return 'Today'
            }
            const dt = new Date(delta)
            let [years, months, days] = [dt.getUTCFullYear() - 1970, dt.getUTCMonth(), dt.getUTCDate()]
            let message = delta > 0 ? '' : '- '
            if (years > 0) {
                message += `${years} years `
            }
            if (months > 0) {
                message += `${months} months `
            }
            if (days > 0) {
                message += `${days} days`
            }
            return message
        }
    },
    methods: {
        refresh_pickers() {
            $(this.$el).find('.selectpicker').selectpicker('redner').selectpicker('refresh')
        },
        get_url() {
            const api_url = this.$root.build_api_url(
                'backend_performance',
                'retention',
                {trailing_slash: true}
            )
            return api_url + this.$root.project_id + '/' + this.result_uid
        },
        async fetch_retention() {

            const resp = await fetch(this.get_url())
            if (resp.ok) {
                const data = await resp.json()
                this.initial_retention = data.retention
                Object.assign(this.$data, this.process_response(data))
            } else {
                showNotify('ERROR', 'Error fetching retention')
            }
        },
        process_response(data) {
            const {retention, ttl, ts, ...rest} = data
            const {time_type, time_amount} = this.process_retention(retention)
            return {time_type, time_amount, ttl, ts, ...rest}
        },
        process_retention(retention_data) {
            if (retention_data === null) {
                return  {time_type: 'unlimited', time_amount: 1}
            }
            const [time_type, time_amount] = Object.entries(retention_data)[0]
            return {time_type, time_amount}
        },
        handle_cancel() {
            Object.assign(this.$data, this.process_retention(this.initial_retention))
        },
        handle_set_default() {
            Object.assign(this.$data, this.process_retention(this.default_retention))
        },
        async handle_save() {
            const timedelta = this.time_type === 'unlimited' ? null : {[this.time_type]: this.time_amount}
            const resp = await fetch(this.get_url(), {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({timedelta})
            })
            if (resp.ok) {
                const data = await resp.json()
                this.initial_retention = data.retention
                Object.assign(this.$data, this.process_response(data))
                showNotify('SUCCESS', 'Retention updated')
            } else {
                showNotify('ERROR', 'Error saving retention')
            }
        }
    },
    // @update:modelValue="window.console.log('qqq', $event)"
    template: `
    <div :id="modal_id" class="modal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered"
             style="min-width: 600px;"
        >
            <div class="modal-content p-0">
<!--                <button class="btn btn-secondary" @click="fetch_retention">fetch</button>-->
                <div class="d-flex justify-content-between align-items-end px-28 pt-24 mb-3">
                    <p class="font-h3 font-bold">Retention policy settings</p>
                </div>
                <div class="px-28">
                    <p v-if="initial_retention !== undefined">
                        This test result will be deleted in: <b>[[ remaining_time ]]</b>
                    </p>
                </div>
                <div class="px-28">
                <label class="d-inline-flex flex-column w-100">
                    <span class="font-h6 mb-1">Retention policy:</span>
                    <div class="d-flex">
                        <select class="selectpicker bootstrap-select__b mr-2 flex-grow-1" 
                            data-style="btn"
                            v-model="time_type"
                        >
                            <option v-for="i in ['days', 'weeks', 'months', 'years', 'unlimited']" 
                                :value="i" 
                                :key="i"
                            >
                                [[ i ]]
                            </option>
                        </select>
                        <input-stepper 
                            v-model="time_amount" 
                            :disabled="time_type === 'unlimited'"
                            v-if="time_type !== 'unlimited'"
                            :uniq_id="modal_id + '_stepper'"
                            :min_value="1"
                        ></input-stepper>
                    </div>
                </label>
                </div>
                <div class="modal-footer mt-24">
                    <button type="button" class="btn btn-sm btn-default" 
                        v-if="default_retention !== undefined"
                        @click="handle_set_default"
                    >
                        Reset to default
                    </button>
                    <span class="flex-grow-1"></span>
                    <button type="button" class="btn btn-secondary" data-dismiss="modal" 
                        @click="handle_cancel"
                    >
                        Cancel
                    </button>
                    <button type="button" class="btn btn-primary"
                        @click="handle_save"
                    >Save</button>
                </div>
            </div>
        </div>
    </div>
    `
}

register_component('RetentionModal', RetentionModal)