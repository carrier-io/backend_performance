from tools import constants as c

JMETER_MAPPING = {
    "v5.6.3": {
        "container": f"getcarrier/perfmeter:{c.CURRENT_RELEASE}-5.6.3",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.5": {
        "container": f"getcarrier/perfmeter:{c.CURRENT_RELEASE}-5.5",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
}

GATLING_MAPPING = {
    "maven": {
        "container": f"getcarrier/gatling_maven_runner:{c.CURRENT_RELEASE}",
        "job_type": "perfgun",
        "influx_db": "{{secret.gatling_db}}"
    },
    "v3.7": {
        "container": f"getcarrier/perfgun:{c.CURRENT_RELEASE}-3.7",
        "job_type": "perfgun",
        "influx_db": "{{secret.gatling_db}}"
    },
}

EXECUTABLE_MAPPING = {
    # "gatling": {
    #     "container": f"getcarrier/executable_jar_runner:{c.CURRENT_RELEASE}-gatling",
    #     "job_type": "perfgun",
    #     "influx_db": "{{secret.gatling_db}}"
    # },
    # "base (in development)": {
    #     "container": f"getcarrier/executable_jar_runner:{c.CURRENT_RELEASE}-base",
    #     "job_type": "perfgun",
    #     "influx_db": "{{secret.gatling_db}}"
    # }
}

JOB_CONTAINER_MAPPING = {
    **JMETER_MAPPING,
    **GATLING_MAPPING,
 #   **EXECUTABLE_MAPPING
}

JOB_TYPE_MAPPING = {
    "perfmeter": "jmeter",
    "perfgun": "gatling",
    "free_style": "other",
    "observer": "observer",
    "dast": "dast",
    "sast": "sast",
}
