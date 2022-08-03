const QualityGate = {
    delimiters: ['[[', ']]'],
    props: ['active', 'failed_thresholds_rate', 'error'],
    emits: ['update:active', 'update:failed_thresholds_rate'],
    template: `
    <div class="card card-x card-row-1">
        <div class="card-header">
            <div class="d-flex">
                <h9 class="flex-grow-1">
                    QualityGate
                </h9>
                <label class="custom-toggle">
                    <input type="checkbox"
                        :checked="active"
                        @change="$emit('update:active', $event.target.checked)"
                    />
                    <span class="custom-toggle_slider round"></span>
                </label>
            </div>
        </div>
        <div class="row">
            <div class="col-12 mb-3 pl-0 collapse" 
                ref="settings"
            >
                <label class="col-12 p-0">
                    <h9>Failed thresholds rate. If the failed thresholds rate in the test is higher than this number, the test will be considered as failed</h9>
                    <input type="number" class="form-control" placeholder="Failed thresholds rate"
                        :value="failed_thresholds_rate"
                        @change="$emit('update:failed_thresholds_rate', $event.target.value)"
                        :class="{ 'is-invalid': !!error }"
                    >
                   <div class="invalid-feedback">[[ error?.msg ]]</div>
                </label>
            </div>
       </div>
    </div>
    `,
    watch: {
        active(newValue) {
            $(this.$refs.settings).collapse(!newValue ? 'hide' : 'show')
        }
    },
    mounted() {
        this.$props.active && $(this.$refs.settings).collapse('show')
    }
}

register_component('QualityGate', QualityGate)
