function updateEnvPicker(_callback) {
    $.get(`/api/v1/backend_performance/environments/${getSelectedProjectId()}`, {
            name: $("#testName").val()
        },
        function(data) {
            $("#envName").empty();
            data.forEach(item => {
                $("#envName").append(`<option value="${item}">${item}</option>`);
            });
            $("#envName").selectpicker('refresh').trigger('change');
            if (_callback !== undefined) {
                _callback();
            }
        });
}

function updateScopePicker() {
    $.get(`/api/v1/backend_performance/requests/${getSelectedProjectId()}`, {
            name: $("#testName").val(),
            env: $("#envName").val()
        },
        function(data) {
            $("#scope").empty();
            $("#scope").append(`<option value="all">all</option>`);
            $("#scope").append(`<option value="every">every</option>`);
            data.forEach(item => {
                $("#scope").append(`<option value="${item}">${item}</option>`);
            });
            $("#scope").selectpicker('refresh').trigger('change');
        });
}

function insertThreshold() {
    $.ajax({
        url: `/api/v1/backend_performance/thresholds/${getSelectedProjectId()}`,
        type: "POST",
        data: JSON.stringify({
            test: $("#testName").val(),
            env: $("#envName").val(),
            scope: $("#scope").val(),
            target: $("#target").val(),
            aggregation: $("#aggregation").val(),
            comparison: $("#comparison").val(),
            value: parseInt($("#th_value").val())
        }),
        contentType: "application/json",
        dataType: "json",
        success: function() {
            $("#threshold-list").bootstrapTable('refresh');
            $("#createThresholdModal").modal('hide');
        }
    });
}

function showEditThreshold(index) {
    $("#createThresholdModal").modal('toggle');
    $("#modal_title").html("Edit Threshold");
    $("#add_threshold").html("Edit");
    setTimeout(updateModalData, 500, index);
}

function updateModalData(index) {
    var data = $("#threshold-list").bootstrapTable('getRowByUniqueId', index);
    $("#testName").selectpicker('val', data['test']);
    updateEnvPicker(() => {
        $("#envName").selectpicker('val', data['environment']);
    });
    $("#scope").selectpicker('val', data['scope']);
    $("#target").selectpicker('val', data['target']);
    $("#aggregation").selectpicker('val', data['aggregation']);
    $("#comparison").selectpicker('val', data['comparison']);
    $("#th_value").val(data['value']);
    $("#add_threshold").attr('onclick', `editThreshold("${index}")`);
}

function deleteThreshold(index, callback) {
    var data = $("#threshold-list").bootstrapTable('getRowByUniqueId', index);
    var request_params = $.param({
        test: data['test'],
        env: data['environment'],
        scope: data['scope'],
        target: data['target'],
        aggregation: data['aggregation'],
        comparison: data['comparison']
    });
    $.ajax({
        url: `/api/v1/backend_performance/thresholds/${getSelectedProjectId()}?` + request_params,
        type: "DELETE",
        contentType: 'application/json',
        success: function() {
            $("#threshold-list").bootstrapTable('refresh');
            if (callback !== undefined) {
                callback()
            }
        }
    })
}

function editThreshold(index) {
    deleteThreshold(index, insertThreshold);
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

function thresholdsActionFormatter(value, row, index) {
    var id = row['id'];
    return `
    <div class="d-flex justify-content-end">
        <button type="button" class="btn btn-24 btn-action" onclick="showEditThreshold('${id}')"><i class="fas fa-cog"></i></button>
        <button type="button" class="btn btn-24 btn-action" onclick="deleteThreshold('` + id + `')"><i class="fas fa-trash-alt"></i></button>
    </div>
    `
}

$(document).on('vue_init', () => {
    $(document).ready(function() {
        updateEnvPicker();

        $('#createThresholdModal').on('hide.bs.modal', function(e) {
            $("#modal_title").html("Create Threshold");
            $("#add_threshold").html("Save");
            $("#add_threshold").attr('onclick', `insertThreshold()`);
            $("#th_value").val("");
        });
    });
})