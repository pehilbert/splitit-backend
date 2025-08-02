class SensitiveSanitizer:
    def __init__(self, logger, sensitive_fields=[]):
        self.sensitive_fields = sensitive_fields
        self.logger = logger

    def sanitize_dict(self, data_dict):
        data_dict = data_dict.copy()

        for field in self.sensitive_fields:
            if field in data_dict:
                if isinstance(data_dict[field], str):
                    data_dict[field] = "[REDACTED]"
                elif isinstance(data_dict[field], list):
                    data_dict[field] = ["[REDACTED]" for _ in data_dict[field]]
                elif isinstance(data_dict[field], dict):
                    data_dict[field] = {k: "[REDACTED]" for k in data_dict[field].keys()}
                else:
                    self.logger.warning(f"Unsupported type for sensitive field '{field}': {type(data_dict[field])}")
                    return
                
                self.logger.debug(f"Sensitive field '{field}' sanitized.")
                data_dict[field] = "[REDACTED]"
                
        return data_dict