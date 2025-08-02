from flask import json, request, current_app

def setup_blueprint(app, blueprint):
    # Log complete request information
    @blueprint.before_request
    def log_request_info():
        query_params = app.sanitizer.sanitize_dict(request.args.to_dict() or {})
        body = app.sanitizer.sanitize_dict(request.get_json(silent=True) or {})

        current_app.logger.info(f"\nRequest: {request.method} {request.path}\n"
                                f"Query Params:\n{json.dumps(query_params, indent=2)}\n"
                                f"Body:\n{json.dumps(body, indent=2)}")
    
    @blueprint.after_request
    def log_response_info(response):
        response_data = response.data
        
        if response.is_json:
            sanitized_response = app.sanitizer.sanitize_dict(response.get_json())
            response_data = json.dumps(sanitized_response, indent=2)

        current_app.logger.info(f"\nResponse: {response.status_code}\nData:\n{response_data}")

        return response
        
    app.register_blueprint(blueprint)
    current_app.logger.info(f"Blueprint {blueprint.name} registered successfully.")