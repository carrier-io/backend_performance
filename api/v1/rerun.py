from flask_restful import Resource


class API(Resource):
    url_params = [
        '<int:security_results_dast_id>',
    ]

    def __init__(self, module):
        self.module = module

    def post(self, security_results_dast_id: int):
        """
        Post method for re-running test
        """

        raise NotImplementedError()

