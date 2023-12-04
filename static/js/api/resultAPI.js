const ApiFetchPreset = async () => {
    const res = await fetch(`/api/v1/backend_performance/summary_table_presets/${getSelectedProjectId()}`,
        {
            method: 'GET',
        })
    return res.json();
}

const ApiAddPreset = async (preset) => {
    const res = await fetch(`/api/v1/backend_performance/summary_table_presets/${getSelectedProjectId()}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(preset)

    })
    return res.json();
}

const ApiUpdatePreset = async (preset) => {
    const res = await fetch(`/api/v1/backend_performance/summary_table_presets/${getSelectedProjectId()}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(preset)

    })
    return res.json();
}

const ApiDeletePreset = async (presetName) => {
    const deletedPreset = 'new';
    await fetch(`/api/v1/backend_performance/summary_table_presets/${getSelectedProjectId()}/${presetName}`, {
        method: 'DELETE',
    })
}