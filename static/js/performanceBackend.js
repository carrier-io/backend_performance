var analyticsData;
var interval_id;

function createTest() {
    $("#submit").addClass("disabled");
    $("#save").addClass("disabled");
    var params = [
        [], {}, {}, {}
    ]
    params[0].push({
        "name": "test_name",
        "default": $('#test_name').val(),
        "description": "Name of the test",
        "type": "",
        "action": ""
    })
    params[0].push({
        "name": "env_type",
        "default": $('#test_env').val(),
        "description": "Env type (tag for filtering)",
        "type": "",
        "action": ""
    })
    params[0].push({
        "name": "test_type",
        "default": $('#test_type').val(),
        "description": "Test type (tag for filtering)",
        "type": "",
        "action": ""
    })
    $("#backend_test_params").bootstrapTable('getData').forEach((param) => {
        params[0].push(param)
    })

    params[1]["cpu_quota"] = $('#backend_cpu').text()
    params[1]["memory_quota"] = $('#backend_memory').val()

    $("#extCard .row").slice(1, ).each(function(_, item) {
        var inp = $(item).find('input[type=text]')
        params[3][inp[0].value] = inp[1].value
    })
    csvFiles = {}
    $("#splitCSV .flex-row").slice(1, ).each(function(_, item) {
        var file = $(item).find('input[type=text]')
        var header = $(item).find('input[type=checkbox]')
        csvFiles[file[0].value] = header[0].checked
    })
    params[3]["csv_files"] = JSON.stringify(csvFiles)
    var compile = $('#compile').is(":checked")
    event.preventDefault();

    var data = new FormData();
    git_settings = {}
    if ($('#repo').val() != '' || $('#repo_https').val() != '') {
        git_settings["repo"] = $('#repo').val() != '' ? $('#repo').val() : $('#repo_https').val()
        git_settings["protocol"] = $('#repo').val() != '' ? 'ssh' : 'https'
        git_settings["repo_user"] = $('#repo_user').val()
        git_settings["repo_pass"] = $('#repo_pass').val()
        git_settings["repo_key"] = $('#repo_key').val()
        git_settings["repo_branch"] = $('#repo_branch').val() ? $('#repo_branch').val() : $('#repo_branch_https').val()
        data.append('git', JSON.stringify(git_settings));
    } else if ($('#file')[0].files[0] != undefined) {
        data.append('file', $('#file')[0].files[0], $('#file')[0].files[0].name);
    } else if ($('#local_file').val() != '') {
        data.append('local_path', $('#local_file').val());
    }


    data.append('name', $('#test_name').val());
    data.append('parallel', $('#backend_parallel').text());
    data.append('region', $('#backend_region option:selected').text());
    data.append('entrypoint', $('#entrypoint').val());
    data.append('runner', $('#runner').val());
    data.append('reporting', JSON.stringify({}));
    data.append('compile', compile);
    data.append('emails', $('#emails').val());
    data.append('params', JSON.stringify(params[0]));
    data.append('env_vars', JSON.stringify(params[1]));
    data.append('customization', JSON.stringify(params[2]));
    data.append('cc_env_vars', JSON.stringify(params[3]));

    $.ajax({
        url: `/api/v1/backend_performance/tests/${getSelectedProjectId()}`,
        data: data,
        cache: false,
        contentType: false,
        processData: false,
        method: 'POST',
        success: function(data) {
            $("#createTestModal").modal('hide');
            $("#tests-list").bootstrapTable('refresh')
        }
    });
}

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


function addDNSOverride(id, key = "", value = "") {
    $(`#${id}`).append(`<div class="row mt-2">
    <div class="col-6 ml-0">
        <input type="text" class="form-control" placeholder="hostname.company.com" value="${key}">
    </div>
    <div class="col">
        <input type="text" class="form-control" placeholder="0.0.0.0" value="${value}">
    </div>
    <div class="col-xs pt-1 text-right">
        <button type="button" class="btn btn-nooutline-secondary mr-2" onclick="removeParam(event)"><i class="fas fa-minus"></i></button>
    </div>
</div>`)
}

function backendLgFormatter(value, row, index) {
    if (row.job_type === "perfmeter") {
        return '<img src="/design-system/static/assets/ico/jmeter.png" width="20">'
    } else if (row.job_type === "perfgun") {
        return '<img src="/design-system/static/assets/ico/gatling.png" width="20">'
    } else {
        return value
    }
}

function thresholdsActionFormatter(value, row, index) {
    var id = row['id'];
    return `
    <div class="d-flex justify-content-end">
        <button type="button" class="btn btn-24 btn-action" onclick="showEditThreshold('${id}')"><i class="fas fa-cog"></i></button>
        <button type="button" class="btn btn-24 btn-action" onclick="deleteThreshold('` + id + `')"><i class="fas fa-trash-alt"></i></button>
    </div>
    `
}

function ruleFormatter(value, row, index) {
    let comparisonMap = new Map([
        ["gte", ">="],
        ["lte", "<="],
        ["lt", "<"],
        ["gt", ">"],
        ["eq", "=="]
    ]);
    comparison = comparisonMap.get(row.comparison)
    return row.aggregation + "(" + row.target + ") " + comparison
}

function createLinkToTest(value, row, index) {
    //    const searchParams = new URLSearchParams(location.search);
    //    searchParams.set('module', 'Result');
    //    searchParams.set('page', 'list');
    //    searchParams.set('project_id', getSelectedProjectId());
    //    searchParams.set('result_test_id', row.id);
    //    searchParams.set('test_id', row.test_uid);
    return `<a class="test form-control-label" href="./results?result_id=${row.id}" role="button">${row.name}</a>`
}

function backendTestActionFormatter(value, row, index) {
    return `
    <div class="d-flex justify-content-end">
        <button type="button" class="btn btn-24 btn-action" onclick="runTestModal('${row.id}')" data-toggle="tooltip" data-placement="top" title="Run Test"><i class="fas fa-play"></i></button>
        <button type="button" class="btn btn-24 btn-action" onclick="editTest('${row.id}')"><i class="fas fa-cog"></i></button>
        <button type="button" class="btn btn-24 btn-action"><i class="fas fa-share-alt"></i></button>
        <button type="button" class="btn btn-24 btn-action" onclick="deleteTests('${row.id}')"><i class="fas fa-trash-alt"></i></button>
    </div>
    `
}

function reportsStatusFormatter(value, row, index) {
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
}

function copyToClipboard(text) {
    var dummy = document.createElement("textarea");
    document.body.appendChild(dummy);
    dummy.value = text;
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);
}


$("#tests-list").on("post-body.bs.table", function(data) {
    $('[data-toggle="tooltip"]').tooltip()
})

function cellStyle(value, row, index) {
    return {
        css: {
            "min-width": "165px"
        }
    }
}

function nameStyle(value, row, index) {
    return {
        css: {
            "max-width": "140px",
            "overflow": "hidden",
            "text-overflow": "ellipsis",
            "white-space": "nowrap"
        }
    }
}

function runTestModal(test_id) {
    $("#runTestModal").modal('show');
    var test_data = $('#tests-list').bootstrapTable('getRowByUniqueId', test_id);
    $('#runner_test_params').bootstrapTable('removeAll')
    test_data.params.forEach((param) => {
        $('#runner_test_params').bootstrapTable('append', param)
    })
    $('#run_test').removeAttr('onclick');
    $('#run_test').attr('onClick', `runTest("${test_data.test_uid}")`);
    $('#runner_region').val(test_data.region)
    $('#runner_parallel').text(test_data.parallel)
    $('#runner_cpu').text(test_data.env_vars["cpu_quota"])
    $('#runner_memory').val(test_data.env_vars["memory_quota"])
}

function editTest(test_id) {
    $("#createTestModal").modal('show');
    var test_data = $('#tests-list').bootstrapTable('getRowByUniqueId', test_id);
    $('#backend_test_params').bootstrapTable('removeAll')
    test_data.params.forEach((param) => {
        if (param['name'] == 'test_name') {
            $('#test_name').val(param['default']);
            $("#test_name").prop("disabled", true);
        } else if (param['name'] == 'test_type') {
            $('#test_type').val(param['default']);
        } else if (param['name'] == 'env_type') {
            $('#test_env').val(param['default']);
        } else {
            $('#backend_test_params').bootstrapTable('append', param)
        }
    })
    $('#submit').removeAttr('onclick');
    $('#submit').attr('onClick', `updateTest("${test_data.test_uid}")`);
    $('#save').removeAttr('onclick');
    $('#save').attr('onClick', `updateTest("${test_data.test_uid}")`);
    $("#testrunners").hide();
    $("#compileTests").hide();
    $("#fileUpload").hide();
    $("#entrypoint").val(test_data.entrypoint);
    $("#entrypoint").prop("disabled", true);
    console.log("*******************")
    console.log(test_data)
    console.log("*******************")
    $('#backend_region').val(test_data.region);
    $('#backend_parallel').text(test_data.parallel);
    $('#backend_cpu').text(test_data.env_vars["cpu_quota"])
    $('#backend_memory').val(test_data.env_vars["memory_quota"])
    if (test_data.git != null && test_data.git.hasOwnProperty("repo")) {
        $("#nav-file-tab").prop("disabled", true);
        if (test_data.git.protocol == "https") {
            $("#nav-git-tab").prop("disabled", true);
            $('a[href="#nav-git-https"]').click();
            $("#repo_https").val(test_data.git.repo);
            $("#repo_branch_https").val(test_data.git.repo_branch);
            $("#repo_user").val(test_data.git.repo_user);
            $("#repo_pass").val(test_data.git.repo_pass);
        } else {
            $("#nav-git-https-tab").prop("disabled", true);
            $('a[href="#nav-git"]').click();
            $("#repo").val(test_data.git.repo);
            $("#repo_branch").val(test_data.git.repo_branch);
            $("#repo_key").val(test_data.git.repo_key);
        }
    } else {
        $("#nav-git-tab").prop("disabled", true);
        $("#nav-git-https-tab").prop("disabled", true);
        $('a[href="#nav-file"]').click();
    }
}

function updateTest(test_id) {
    $("#submit").addClass("disabled");
    $("#save").addClass("disabled");
    var params = [
        [], {}, {}, {}
    ]
    params[0].push({
        "name": "test_name",
        "default": $('#test_name').val(),
        "description": "Name of the test",
        "type": "",
        "action": ""
    })
    params[0].push({
        "name": "env_type",
        "default": $('#test_env').val(),
        "description": "Env type (tag for filtering)",
        "type": "",
        "action": ""
    })
    params[0].push({
        "name": "test_type",
        "default": $('#test_type').val(),
        "description": "Test type (tag for filtering)",
        "type": "",
        "action": ""
    })
    $("#backend_test_params").bootstrapTable('getData').forEach((param) => {
        params[0].push(param)
    })

    params[1]["cpu_quota"] = $('#backend_cpu').text()
    params[1]["memory_quota"] = $('#backend_memory').val()

    $("#extCard .row").slice(1, ).each(function(_, item) {
        var inp = $(item).find('input[type=text]')
        params[3][inp[0].value] = inp[1].value
    })

    var data = {}
    git_settings = {}
    if ($('#repo').val() != '' || $('#repo_https').val() != '') {
        git_settings["repo"] = $('#repo').val() != '' ? $('#repo').val() : $('#repo_https').val()
        git_settings["protocol"] = $('#repo').val() != '' ? 'ssh' : 'https'
        git_settings["repo_user"] = $('#repo_user').val()
        git_settings["repo_pass"] = $('#repo_pass').val()
        git_settings["repo_key"] = $('#repo_key').val()
        git_settings["repo_branch"] = $('#repo_branch').val() ? $('#repo_branch').val() : $('#repo_branch_https').val()
        data['git'] = JSON.stringify(git_settings);
    }

    data['name'] = $('#test_name').val();
    data['parallel'] = $('#backend_parallel').text();
    data['region'] = $('#backend_region option:selected').text();
    data['entrypoint'] = $('#entrypoint').val();
    data['reporting'] = JSON.stringify({});
    data['emails'] = $('#emails').val();
    data['params'] = JSON.stringify(params[0]);
    data['env_vars'] = JSON.stringify(params[1]);
    data['customization'] = JSON.stringify(params[2]);
    data['cc_env_vars'] = JSON.stringify(params[3]);

    $.ajax({
        url: `/api/v1/backend_performance/test/${getSelectedProjectId()}/${test_id}`,
        data: JSON.stringify(data),
        cache: false,
        contentType: 'application/json',
        method: 'PUT',
        success: function(data) {
            $("#createTestModal").modal('hide');
        }
    });
}

function deleteTests(id) {
    var tests = `/api/v1/backend_performance/tests/${getSelectedProjectId()}?`;
    if (id == undefined) {
        $("#tests-list").bootstrapTable('getSelections').forEach(item => {
            tests += "id[]=" + item["id"] + "&"
        });
    } else {
        tests += `id[]=${id}&`
    }
    $.ajax({
        url: tests.substring(0, tests.length - 1),
        type: 'DELETE',
        success: function(result) {
            $("#tests-list").bootstrapTable('refresh');
        }
    });
}

function deleteReports() {
    var reports = `/api/v1/backend_performance/reports/${getSelectedProjectId()}?`;
    $("#results-list").bootstrapTable('getSelections').forEach(item => {
        reports += "id[]=" + item["id"] + "&"
    });
    $.ajax({
        url: reports.substring(0, reports.length - 1),
        type: 'DELETE',
        success: function(result) {
            $("#results-list").bootstrapTable('refresh');
        }
    });
}

function refreshTable(tableID) {
    $(`#${tableID}`).bootstrapTable('refresh');
}

function runTest(test_id) {
    var params = []
    $("#runner_test_params").bootstrapTable('getData').forEach((param) => {
        params.push(param)
    })
    $("#nav-test-params .test_param").each(function() {
        if ($(this).children()[0].innerText !== "" && $(this).children()[1].value !== "") {
            params[$(this).children()[0].innerText] = $(this).children()[1].value;
        }
    });
    var env_vars = {}
    env_vars["cpu_quota"] = $('#runner_cpu').text()
    env_vars["memory_quota"] = $('#runner_memory').val()
    var cc_env_vars = {}
    $("#nav-cc-env-vars .cc_env_vars").each(function() {
        if ($(this).children()[0].innerText !== "" && $(this).children()[1].value !== "") {
            cc_env_vars[$(this).children()[0].innerText] = $(this).children()[1].value;
        }
    });
    var data = {
        'params': JSON.stringify(params),
        'env_vars': JSON.stringify(env_vars),
        'cc_env_vars': JSON.stringify(cc_env_vars),
        'parallel': $('#runner_parallel').text(),
        "type": '',
        'region': $('#runner_region').val()
    }
    $.ajax({
        url: `/api/v1/backend_performance/test/${getSelectedProjectId()}/${test_id}`,
        data: JSON.stringify(data),
        contentType: 'application/json',
        type: 'POST',
        success: function(result) {
            $("#runTestModal").modal('hide');
            $("#results-list").bootstrapTable('refresh')
        }
    });
}


function setParams() {
    build_id = document.querySelector("[property~=build_id][content]").content;
    testId = document.querySelector("[property~=test_id][content]").content;
    lg_type = document.querySelector("[property~=lg_type][content]").content;
    test_name = document.querySelector("[property~=test_name][content]").content;
    environment = document.querySelector("[property~=environment][content]").content;
    samplerType = $("#sampler").val().toUpperCase();
    statusType = $("#status").val().toLowerCase();
    aggregator = $("#aggregator").val().toLowerCase();
}


function fillSummaryTable() {
    $.get(
        '/api/v1/backend_performance/charts/requests/table', {
            build_id: build_id,
            test_name: test_name,
            lg_type: lg_type,
            sampler: samplerType,
            status: statusType,
            start_time: $("#start_time").html(),
            end_time: $("#end_time").html(),
            low_value,
            high_value,
        },
        function(data) {
            data.forEach((item) => {
                $('#summary_table').bootstrapTable('append', item)
            })
        });
}

function loadRequestData(url, y_label) {
    if (!$("#preset").is(":visible")) {
        $("#preset").show();
        $("#analytics").hide();
        if (analyticsLine != null) {
            analyticsLine.destroy();
        }
    }
    // if ($("#end_time").html() != "") {
    //     $("#PP").hide();
    // }
    $.get(
        url, {
            build_id: build_id,
            test_name: test_name,
            lg_type: lg_type,
            sampler: samplerType,
            aggregator: aggregator,
            status: statusType,
            start_time: $("#start_time").html(),
            end_time: $("#end_time").html(),
            low_value,
            high_value,
        },
        function(data) {
            const lineChartData = data;
            if (window.presetLine != null) {
                window.presetLine.destroy();
            }
            drawCanvas(y_label, lineChartData);
            document.getElementById('chartjs-custom-legend').innerHTML = window.presetLine.generateLegend();
        }
    );
}

function displayAnalytics() {
    console.log("displayAnalytics ***************")
    $("#preset").hide();
    analyticsCanvas();
    $("#analytics").show();
    if(window.presetLine!=null){
        window.presetLine.destroy();
    }
    if ( ! $("#analytics").is(":visible") ) {
        console.log("Here")
    }
}

function getData(scope, request_name) {
    if (! $(`#${request_name}_${scope}`).is(":checked")) {
        findAndRemoveDataSet(`${request_name}_${scope}`);
    } else {
        getDataForAnalysis(scope, request_name)
    }
}

function findAndRemoveDataSet(dataset_name){
    for (var i=0; i<analyticsLine.data.datasets.length; i++) {
        if (analyticsLine.data.datasets[i].label === dataset_name) {
            analyticsLine.data.datasets.splice(i, 1);
            analyticsLine.update();
            break;
        }
    }
}

function switchSampler() {
    samplerType = $("#sampler").val().toUpperCase();
    resizeChart();
}

function switchStatus() {
    statusType = $("#status").val().toLowerCase();
    resizeChart();
}

function switchAggregator() {
    aggregator = $("#aggregator").val();
    resizeChart();
}

function selectOrUnselectRequests() {
    if ($('#all_checkbox').is(":checked")) {
        $('.custom__checkbox').each(function(i, ch) {
            if (ch.id != "all_checkbox") {
                $('#' + ch.id).prop('checked', true);
                updateHiddenProperty(false);
            }
        });
    } else {
        $('.custom__checkbox').each(function(i, ch) {
            if (ch.id != "all_checkbox") {
                $('#' + ch.id).prop('checked', false);
                updateHiddenProperty(true);
            }
        });
    }
}

function updateHiddenProperty(hidden) {
    var ci = window.presetLine;
    for (let index = 1; index < ci.data.datasets.length; ++index) {
        var curr = ci.data.datasets[index]._meta;
        curr = Object.values(curr)[0]
        curr.hidden = hidden
    }
    ci.update();
}

updateChart = function(e, datasetIndex) {
    $('#all_checkbox').prop('checked', false);
    var index = datasetIndex;
    var ci = e.view.presetLine;
    var curr = ci.data.datasets[index]._meta;
    curr = Object.values(curr)[0]
    curr.hidden = !curr.hidden
    ci.update();
};

function analyticsCanvas() {
    console.log("analyticsCanvas ******************")
    var analyticsContext=document.getElementById("chart-analytics").getContext("2d");
    analyticsLine = Chart.Line(analyticsContext, {
        data: analyticsData,
        options: {
            responsive: true,
            hoverMode: 'index',
            stacked: false,
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    fontSize: 10,
                    usePointStyle: false
                }
            },
            title:{
                display: false,
            },
            scales: {
                yAxes: [{
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "left",
                    scaleLabel: {
                        display: true,
                        labelString: "Response Time, ms"
                    },
                    id: "time",
                }, {
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "right",
                    scaleLabel: {
                        display: true,
                        labelString: "Count"
                    },
                    id: "count",
                    gridLines: {
                        drawOnChartArea: false, // only want the grid lines for one axis to show up
                    },
                }],
            }
        }
    });
}

function drawCanvas(y_label, chartData) {
    const presetsContext = document.getElementById("chart-requests").getContext("2d");
    window.presetLine = Chart.Line(presetsContext, {
        data: chartData,
        options: {
            responsive: true,
            hoverMode: 'index',
            stacked: false,
             legendCallback: function (chart) {
                var legendHtml = [];
                for (var i=0; i<chart.data.datasets.length; i++) {
                    if (chart.data.datasets[i].label != "Active Users") {
                        var cb = '<div class="d-flex mb-3">';
                        cb += '<label class="mb-0 w-100 d-flex align-items-center custom-checkbox custom-checkbox__multicolor">'
                        cb += '<input class="mx-2 custom__checkbox" id="'+ chart.legend.legendItems[i].datasetIndex +'" type="checkbox" checked="true" style="--cbx-color: ' + chart.data.datasets[i].backgroundColor + ';" '
                        cb += 'onclick="updateChart(event, ' + '\'' + chart.legend.legendItems[i].datasetIndex + '\'' + ')"/>';
                        cb += '<span class="custom-chart-legend-span"></span>'
                        cb += chart.data.datasets[i].label;
                        cb += '</label></div>'
                        legendHtml.push(cb);
                    }
                }
                return legendHtml.join("");
            },
            legend: {
                display: false,
                position: 'right',
                labels: {
                    fontSize: 10,
                    usePointStyle: false
                }
            },
            title: {
                display: false,
            },
            scales: {
                xAxes: [{
                    gridLines: {
                        display: false
                    }
                }],
                yAxes: [{
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "left",
                    scaleLabel: {
                        display: true,
                        labelString: y_label
                    },
                    id: "response_time",
                    gridLines: {
                        borderDash: [2, 1],
                        color: "#D3D3D3"
                    },
                    ticks: {
                        beginAtZero: true,
                        maxTicksLimit: 10
                    },
                }, {
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "right",
                    gridLines: {
                        display: false
                    },
                    ticks: {
                        beginAtZero: true,
                        maxTicksLimit: 10
                    },
                    id: "active_users",
                }],
            }
        }
    });
}

function fillErrorTable() {
    var start_time = $("#start_time").html()
    var end_time = $("#end_time").html()
    test_name = document.querySelector("[property~=test_name][content]").content;
    $('#errors').bootstrapTable('refreshOptions', {
        url: `/api/v1/backend_performance/charts/errors/table?test_name=${test_name}&start_time=${start_time}&end_time=${end_time}&low_value=${low_value}&high_value=${high_value}`
    })
}

function getDataForAnalysis(metric, request_name) {
$.get(
  '/api/v1/backend_performance/charts/requests/data',
  {
    scope: [request_name],
    metric: metric,
    build_id: build_id,
    test_name: test_name,
    lg_type: lg_type,
    sampler: samplerType,
    aggregator: aggregator,
    status: statusType,
    start_time: $("#start_time").html(),
    end_time: $("#end_time").html(),
    low_value: $("#input-slider-range-value-low").html(),
    high_value: $("#input-slider-range-value-high").html()
  },
  function( data ) {
    if (analyticsLine.data.labels.length == 0 || analyticsLine.data.labels.length != data.labels.length)
    {
        analyticsData = data;
        analyticsCanvas();
    } else {
        analyticsLine.data.datasets.push(data.datasets[0]);
        analyticsLine.update();
    }
  }
 );
}

function resizeChart() {
    if ($("#analytics").is(":visible")) {
        analyticsData = null;
        analyticsLine.destroy();
        analyticsCanvas();
        recalculateAnalytics();
    }
    ["RT", "AR", "HT", "AN"].forEach(item => {
        if ($(`#${item}`).hasClass("active")) {
            $(`#${item}`).trigger("click");
        }
    });
    fillErrorTable();
}

function recalculateAnalytics() {
    var iterator = document.evaluate("//div[@id='analytics']//input[@type='checkbox']", document, null, XPathResult.UNORDERED_NODE_ITERATOR_TYPE, null );
    var el = iterator.iterateNext();
    var arr = []
    while (el) {
        if (el.checked) {
            arr.push(el)
        }
        el = iterator.iterateNext();
    }
    arr.forEach(el => el.onchange());
}


function detailFormatter(index, row) {
    var html = []
    html.push('<p><b>Method:</b> ' + row['Method'] + '</p>')
    html.push('<p><b>Request Params:</b> ' + row['Request params'] + '</p>')
    html.push('<p><b>Headers:</b> ' + row['Headers'] + '</p>')
    html.push('<p><b>Response body:</b></p>')
    html.push('<textarea disabled style="width: 100%">' + row['Response body'] + '</textarea>')
    return html.join('')
}

function showConfig() {
    //TODO
    console.log("show test config")
}

function rerunTest() {
    //TODO
    console.log("rerun test with the same config")
}

function setBaseline() {
    var data = {
        test_name: test_name,
        env: environment,
        build_id: build_id
    };

    $.ajax({
        url: `/api/v1/backend_performance/baseline/${getSelectedProjectId()}`,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data)
    });
}

function compareWithBaseline() {
    console.log("here")
    $.get(
        `/api/v1/backend_performance/baseline/${getSelectedProjectId()}`, {
            test_name: test_name,
            env: environment
        },
        function(data) {
            if (data['baseline'].length != 0) {
                var baseline_id = data['report_id']
                const queryString = window.location.search;
                const urlParams = new URLSearchParams(queryString);
                var report_id = urlParams.get('result_test_id');
                if (report_id == baseline_id) {
                    console.log("Current test is Baseline")
                    $("#compare_with_baseline").html('Current test is Baseline');
                } else {
                    // TODO add comparison page
                    //var url = window.location.origin + "/report/compare?id[]=" + baseline_id + "&id[]=" + report_id;
                    //window.location.href = url;
                    console.log("Compare two reports")
                    $("#compare_with_baseline").html('Compare two reports');
                }

            } else {
                console.log("Baseline is not set yet")
                $("#compare_with_baseline").html('Baseline is not set yet');
            }
        }
    );
}

function setThresholds() {
    //TODO
    console.log("set current report results as threshold")
}

function downloadReport() {
    //TODO
    console.log("download test report")
}

function shareTestReport() {
    //TODO
    console.log("share test report")
}

function stopTest() {
    data = {
        "test_status": {
            "status": "Canceled",
            "percentage": 100,
            "description": "Test was canceled"
        }
    }
    $.ajax({
        url: `/api/v1/backend_performance/report_status/${getSelectedProjectId()}/${testId}`,
        data: JSON.stringify(data),
        contentType: 'application/json',
        type: 'PUT',
        success: function(result) {
            document.location.reload();
        }
    });
}

function auto_update() {
    var interval = parseInt($('#auto_update').val())
    if (interval_id != null || interval == 0) {
        clearInterval(interval_id);
    }
    if (interval != 0) {
        interval_id = setInterval(function() {
            updateChartAndErrorsTable(interval_id);
        }, interval);
    }
}

function updateChartAndErrorsTable(interval_id) {
    if ($("#sampler").val() == null) {
        samplerType = "Request"
    } else {
        samplerType = $("#sampler").val().toUpperCase();
    }

    statusType = $("#status").val().toLowerCase();
    aggregator = $("#aggregator").val().toLowerCase();

    $.get(
    `/api/v1/backend_performance/report_status/${getSelectedProjectId()}/${testId}`,
    function(data) {
        var status = data["message"]
        if (!['finished', 'error', 'failed', 'success'].includes(status.toLowerCase())) {
            const sections = ['#RT', '#AR', '#HT', "#AN"];
            sections.forEach(element => {
                if ($(element).hasClass("active")) {
                    $(element).trigger( "click" )
                }
            });
            fillErrorTable();
        } else {
            clearInterval(interval_id);
        }
    });
}