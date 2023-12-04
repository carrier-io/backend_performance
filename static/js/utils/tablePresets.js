const defaultPresetsTableData = [
    {
        title: "request name",
        field: "request_name",
        checked: true,
    },
    {
        title: "total",
        field: "total",
        checked: true,
    },
    {
        title: "throughput",
        field: "throughput",
        checked: true,
    },
    {
        title: "errors",
        field: "ko",
        checked: true,
    },
    {
        title: "min",
        field: "min",
        checked: true,
    },
    {
        title: "max",
        field: "max",
        checked: true,
    },
    {
        title: "medium",
        field: "mean",
        checked: true,
    },
    {
        title: "pct50",
        field: "pct50",
        checked: false,
    },
    {
        title: "pct75",
        field: "pct75",
        checked: false,
    },
    {
        title: "pct90",
        field: "pct90",
        checked: false,
    },
    {
        title: "pct95",
        field: "pct95",
        checked: true,
    },
    {
        title: "pct99",
        field: "pct99",
        checked: false,
    },
    {
        title: "1xx",
        field: "1xx",
        checked: false,
    },
    {
        title: "2xx",
        field: "2xx",
        checked: false,
    },
    {
        title: "3xx",
        field: "3xx",
        checked: false,
    },
    {
        title: "4xx",
        field: "4xx",
        checked: false,
    },
    {
        title: "5xx",
        field: "5xx",
        checked: false,
    },
    {
        title: "NaN",
        field: "NaN",
        checked: false,
    },
    {
        title: "duration",
        field: "duration",
        checked: false,
    },
    {
        title: "env",
        field: "env",
        checked: false,
    },
    {
        title: "simulation",
        field: "simulation",
        checked: false,
    },
    {
        title: "test type",
        field: "test_type",
        checked: false,
    }
]

const tableSummaryColumns = defaultPresetsTableData.map(col => {
    return {
        title: col.title,
        field: col.title,
        sortable: true,
    }
})

const defaultPreset = {
    "name": "default",
    "fields": defaultPresetsTableData.filter(col => col.checked).map(field => field.field),
}

const allFields = defaultPresetsTableData.map(col => col.field)

