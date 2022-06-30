from ..shared.tools.constants import CURRENT_RELEASE


JOB_CONTAINER_MAPPING = {
    "v5.5": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.5",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.4.1": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.4.1",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.3": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.3",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.2.1": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.2.1",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.2": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.2",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.1.1": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.1.1",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.1": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.1",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.0": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.0",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v4.0": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-4.0",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v3.1": {
        "container": f"getcarrier/perfgun:{CURRENT_RELEASE}-3.1",
        "job_type": "perfgun",
        "influx_db": "{{secret.gatling_db}}"
    },
    "v2.3": {
        "container": f"getcarrier/perfgun:{CURRENT_RELEASE}-2.3",
        "job_type": "perfgun",
        "influx_db": "{{secret.gatling_db}}"
    }
}

JOB_TYPE_MAPPING = {
    "perfmeter": "jmeter",
    "perfgun": "gatling",
    "free_style": "other",
    "observer": "observer",
    "dast": "dast",
    "sast": "sast",
}
