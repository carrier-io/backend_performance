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
                const {error_rate, degradation_rate, missed_thresholds} = this
                return {error_rate, degradation_rate, missed_thresholds}
            }
        },
        set_data(data) {
            console.log('set_data', data)
            const {id, ...rest} = data
            this.load(rest)
            this.$emit('set_data', {id: 'quality_gate'})
        },
        clear_data() {
            Object.assign(this.$data, this.initialState())
            this.$emit('clear_data')
        },
        load(data) {
            Object.assign(this.$data, {...this.initialState(), ...data})
        },
        set_error(data) {
            this.errors[data.loc[data.loc.length - 1]] = data.msg
        },
        clear_errors() {
            this.errors = {}
        },
        initialState: () => ({
            error_rate: 10,
            degradation_rate: 20,
            missed_thresholds : 50,
            errors: {},
        })
    },
    template: `
    <div class="row">
        <div class="d-flex gap-3" 
            ref="settings"
        >
            <div>
                <p class="font-h6 font-semibold">Error rate, %</p>
                <input type="number" class="form-control mt-1" placeholder="Error rate"
                    v-model="error_rate"
                    :class="{ 'is-invalid': errors.error_rate }"
                >
                <div class="invalid-feedback">[[ errors.error_rate ]]</div>
            </div>
            
            <div>
                <p class="font-h6 font-semibold">Degradation rate, %</p>
                <input type="number" class="form-control mt-1" placeholder="Degradation rate"
                    v-model="degradation_rate"
                    :class="{ 'is-invalid': errors.degradation_rate }"
                >
                <div class="invalid-feedback">[[ errors.degradation_rate ]]</div>
            </div>
            
            <div>
                <p class="font-h6 font-semibold">Missed thresholds, %</p>
                <input type="number" class="form-control mt-1" placeholder="Missed thresholds"
                    v-model="missed_thresholds"
                    :class="{ 'is-invalid': errors.missed_thresholds }"
                >
                <div class="invalid-feedback">[[ errors.missed_thresholds ]]</div>
            </div>
        </div>
    </div>
    `,
}

register_component('quality-gate', QualityGate)
