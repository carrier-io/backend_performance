const LogLine = {
    props: ['timestamp', 'host_color', 'hostname', 'log_level', 'message', 'message_class'],
    delimiters: ['[[', ']]'],
    computed: {
        string_ts() {
            return this.timestamp.toLocaleString()
        },
        log_level_class() {
            return `colored-log__${this.log_level}`
        }
    },
    template: `
        <tr>
            <td>[[ string_ts ]]</td>
            <td><span :style="{'color': host_color}" class="ml-4">[[ hostname ]]</span></td>
            <td><span class="colored-log" :class="log_level_class">[[ log_level ]]</span></td>
            <td :class="message_class">[[ message ]]</td>
        </tr>
    `
}

const PerformanceLogsApp = {
    delimiters: ['[[', ']]'],
    props: ['project_id', 'report_id'],
    components: {
        LogLine: LogLine
    },
    data() {
        return {
            state: 'disconnected',
            websocket: undefined,
            states: {
                connecting: 'connecting',
                connected: 'connected',
                disconnected: 'disconnected',
                error: 'error'
            },
            connection_max_retries: 5,
            connection_retry_timeout: 3000,
            connection_retry: 0,
            logs: [],
            follow_logs: true,
            logs_limit: 100,
            tag_map: {},
            tag_colors: [
                '#f89033',
                '#e127ff',
                '#2BD48D',
                '#2196C9',
                '#6eaecb',
                '#385eb0',
                '#7345fc',
                '#94E5B0',
            ].reverse()
        }
    },
    mounted() {
        $(document).on('vue_init', this.init_websocket)
    },
    computed: {
        // reversedLogs: function () {
        //     return this.logs.reverse()
        // },
        websocket_api_url() {
            const base_url = this.$root.build_api_url(
                'backend_performance',
                'loki_url',
                {trailing_slash: true}
            )
            const result_url = new URL(base_url + this.project_id, location.origin)
            result_url.searchParams.append('report_id', this.report_id)
            return result_url
        },
    },
    watch: {
        follow_logs(newValue) {
            if (newValue) {
                this.scrollLogsToEnd()
            }
        },
        logs_limit(newValue, oldValue) {
            if (newValue !== null) {
                if (oldValue !== null && newValue > oldValue) {
                    this.state === this.states.connected && this.websocket.close()
                } else {
                    this.logs = this.logs.slice(-newValue)
                }
            } else {
                this.state === this.states.connected && this.websocket.close()
            }
        },
        async state(newValue) {
            switch (newValue) {
                case this.states.disconnected:
                    if (this.connection_retry > this.connection_max_retries) {
                        console.error(`failed to init websocket after ${this.connection_max_retries} retries`)
                    } else {
                        await this.init_websocket()
                    }
                    break
                case this.states.error:
                    await new Promise(resolve => setTimeout(resolve, this.connection_retry_timeout))
                    break
                case this.states.connecting:
                    this.connection_retry++
                    break
                default:
            }
            console.log('Websocket status:', newValue)
        }
    },
    methods: {
        scrollLogsToEnd() {
            this.$refs.log_container.scrollTop = this.$refs.log_container.scrollHeight
        },
        resolve_color(hostname) {
            let host_color = this.tag_map[hostname]
            if (host_color === undefined) {
                host_color = this.tag_colors.pop()
                if (host_color === undefined) {
                    host_color = '#' + Math.floor(Math.random() * 16777215).toString(16)
                }
                this.tag_map[hostname] = host_color
            }
            return host_color
        },
        async init_websocket() {
            this.state = this.states.connecting
            const resp = await fetch(this.websocket_api_url)
            if (resp.ok) {
                const {websocket_url} = await resp.json()
                this.websocket = new WebSocket(websocket_url)
                this.logs = []
                this.websocket.onmessage = this.on_websocket_message
                this.websocket.onopen = this.on_websocket_open
                this.websocket.onclose = this.on_websocket_close
                this.websocket.onerror = this.on_websocket_error
            } else {
                this.state = this.states.disconnected
                console.warn('Websocket failed to initialize', resp)
            }
        },
        on_websocket_open(message) {
            this.state = this.states.connected
            this.connection_retry = 0
        },
        on_websocket_message(message) {
            if (message.type !== 'message') {
                console.log('Unknown message', message)
                return
            }
            const data = JSON.parse(message.data)
            data.streams.forEach((stream_item, streamIndex) => {
                const host_color = this.resolve_color(stream_item.stream.hostname)
                stream_item.values.forEach((message_item, messageIndex) => {
                    const d = new Date(Number(message_item[0]) / 1000000)

                    if (stream_item.stream.filename === "/tmp/jmeter_logs.log") {
                        const [log_level, ...message_parts] = message_item[1].split(' ').slice(2)
                        this.handle_new_log_line({
                            timestamp: d,
                            host_color: host_color,
                            hostname: stream_item.stream.hostname,
                            log_level: log_level,
                            message: message_parts.join(' '),
                            message_class: ''
                        })
                    } else if (stream_item.stream.filename == null) {
                        this.handle_new_log_line({
                            timestamp: d,
                            host_color: host_color,
                            hostname: stream_item.stream.hostname,
                            log_level: stream_item.stream.level,
                            message: message_item[1],
                            message_class: `log-message__${streamIndex}-${messageIndex}`
                        })
                    }
                    this.follow_logs && this.scrollLogsToEnd()
                })
            })
        },
        on_websocket_close(message) {
            this.state = this.states.disconnected
        },
        on_websocket_error(message) {
            this.state = this.states.error
            this.websocket.close()
        },
        handle_new_log_line(log_data) {
            this.logs.push(log_data)
            this.logs_limit !== null && this.logs.length > this.logs_limit && this.logs.shift()
        }
    },
    template: `
        <div class="card card-12 pb-4 card-table">
            <div class="card-header">
                <div class="d-flex justify-content-between">
                    <p class="font-h3 font-bold">Logs</p>
                    <div class="d-flex">
                        <div class="selectpicker-titled">
                            <span class="font-h6 font-semibold px-3 item__left text-uppercase">
                                Limit logs
                            </span>
<!--                            data-style="btn-secondary" -->
                            <select class="selectpicker" 
                                data-style="item__right"
                                v-model="logs_limit"
                            >
                            <option v-for="i in [10, 100, 500, 1000]" :value="i" :key="i">[[ i ]]</option>
                            <option :value="null">None</option>
                        </select>
                        </div>
                        
                        <label class="custom-checkbox d-flex align-items-center ml-2">
                            <input type="checkbox" 
                                v-model="follow_logs"
                            >
                                <span class="ml-2">Follow logs</span>
                        </label>
                    </div>
                </div>
            </div>
            <div class="card-body card-table">
                <div class="container-logs" ref="log_container">
                    <table class="table-logs">
                        <LogLine v-for="r in logs" v-bind="r"></LogLine>
                    </table>
                </div>
            </div>
        </div>
    `,
}


register_component('PerformanceLogsApp', PerformanceLogsApp)
