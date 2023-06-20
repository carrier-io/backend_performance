const PerformanceTestProgress = {
    delimiters: ['[[', ']]'],
    props: ['test_status', 'project_id', 'test_id'],
    template: `
    <div class="card-body space-progress mt-24 p-3">
        <div style="width: 400px" class="d-flex flex-column m-auto">
            <p class="font-h5 font-bold mb-1" id="test_status_status">
                [[ status ]]
            </p>
            <div class="progress mb-3">
                <div
                    class="progress-bar progress-bar-striped bg-success progress-bar-animated"
                    role="progressbar"
                    aria-valuenow="percentage"
                    :style="{ width: percentage + '%' }"
                    aria-valuemin="0"
                    aria-valuemax="100"
                >
                </div>
            </div>
        </div>
        <p class="font-h5 font-weight-400 text-gray-700 test_status_description text-center">
            [[ description ]]
        </p>
    </div>
    `,
    data() {
        return {
            status: '',
            percentage: 0,
            description: ''
        }
    },
    mounted() {
        const {status, percentage, description} = this.test_status
        this.status = status
        this.percentage = percentage
        this.description = description
        this.poll_intrvl = setInterval(() => this.poll_updates(), 5000)
    },
    methods: {
        async poll_updates() {
            const response = await fetch(`/api/v1/backend_performance/reports/${this.project_id}/?report_id=${this.test_id}`)
            const {test_status: {status, percentage, description}} = await response.json()
            this.status = status
            this.percentage = percentage
            this.description = description
        }
    },
    watch: {
        percentage(newValue, oldValue) {
            if (this.status.toLowerCase() === 'canceled') {
                return
            }
            if (newValue === 100) {
                clearInterval(this.poll_intrvl)
                location.reload()
            }
        }
    }
}

register_component('performancetestprogress', PerformanceTestProgress)