const PerformanceLogsApp = {
    delimiters: ['[[', ']]'],
    props: ['project_id', 'report_id'],
    data() {
        return {
            websocket_api_url: '',
            state: 'unknown',
            websocket: undefined,
            connection_retries: 5,
            connection_retry_timeout: 2000,
            logs: []
        }

    },
    mounted() {
      console.log("Logs: mounted()")
      this.websocket_api_url = `/api/v1/backend_performance/loki_url/${this.project_id}/?report_id=${this.report_id}`
      this.init_websocket()
    },
    // updated() {
    //     var item = $("#logs-body");
    //     item.scrollTop(item.prop("scrollHeight"));
    // },
    computed: {
        reversedLogs: function () {
            return this.logs.reverse()
        },
    },
    template: `
        <div class="card card-12 pb-4 card-table">
            <div class="card-header">
                <div class="row">
                    <div class="col-2"><h3>Logs</h3></div>
                </div>
            </div>
            <div class="card-body card-table">
              <div id="logs-body" class="card-body overflow-auto pt-0 pl-3">
                <textarea class="form-control" id="TerminalTextArea" style="height: 500px;"></textarea>
              </div>
            </div>
        </div>
    `,
    methods: {
        init_websocket() {
            console.log("Logs: init_websocket()")
            fetch(this.websocket_api_url, {
                method: 'GET'
            }).then(response => {
                if (response.ok) {
                    response.json().then(data => {
                      this.websocket = new WebSocket(data.websocket_url)
                      this.websocket.onmessage = this.on_websocket_message
                      this.websocket.onopen = this.on_websocket_open
                      this.websocket.onclose = this.on_websocket_close
                      this.websocket.onerror = this.on_websocket_error
                    })
                } else {
                    console.warn('Websocket failed to initialize', response)
                }
            })
        },
        on_websocket_open(message) {
            this.state = 'connected'
        },
        on_websocket_message(message) {
            if (message.type !== 'message') {
                console.log('Unknown message', message)
                return
            }

            const data = JSON.parse(message.data)

            data.streams.forEach(stream_item => {
                stream_item.values.forEach(message_item => {
                    if (stream_item.stream.filename == "/tmp/jmeter_logs.log") {
                        d = new Date(Number(message_item[0])/1000000)
                        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
                        var timestamp = d.toLocaleString("en-GB", {timeZone: tz})
                        var message = message_item[1].split(" ")
                        message = message.slice(2).join(" ")
                        $('#TerminalTextArea').append(`${timestamp} [${stream_item.stream.hostname}]  ${message}\n`)
                        $('#TerminalTextArea').scrollTop($('#TerminalTextArea')[0].scrollHeight);
                        //this.logs.push(`Source: ${stream_item.stream.hostname} | ${timestamp} ${message}`)
                    }

                })
            })
        },
        on_websocket_close(message) {
            this.state = 'disconnected'
            let attempt = 1;
            const intrvl = setInterval(() => {
                this.init_websocket()
                if (this.state === 'connected' || attempt > this.connection_retries) clearInterval(intrvl)
                attempt ++
            }, this.connection_retry_timeout)
            // setTimeout(websocket_connect, 1 * 1000);
            //    clearInterval(websocket_connect)
        },
        on_websocket_error(message) {
            this.state = 'error'
            this.websocket.close()
        }

    }
}

// Vue.createApp({
//     components: LogsApp
// }).mount('#logs')
//vueApp.component('performancelogsapp', PerformanceLogsApp)
register_component('performancelogsapp', PerformanceLogsApp)
