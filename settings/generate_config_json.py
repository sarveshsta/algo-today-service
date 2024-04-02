import json
from datetime import datetime, time, timedelta


def generate_json(config, config_indicators):
    config_dict = {}

    for name in dir(config):
        if name.isupper():
            var = getattr(config, name)
            var_type = type(var)

            if isinstance(var, datetime):
                var = var.isoformat()
            elif isinstance(var, timedelta):
                var = str(var)
            elif isinstance(var, time):
                var = var.isoformat()
            elif isinstance(var, list):
                var = [str(x) for x in var]  # Convert each list element to string

            config_dict[name] = var
            #print(f"{name}: {var_type}")

    for name in dir(config_indicators):
        if name.isupper():
            var = getattr(config_indicators, name)
            var_type = type(var)

            if isinstance(var, datetime):
                var = var.isoformat()
            elif isinstance(var, timedelta):
                var = str(var)
            elif isinstance(var, time):
                var = var.isoformat()
            elif isinstance(var, list):
                var = [str(x) for x in var]  # Convert each list element to string

            config_dict[name] = var
            print(f"{name}: {var_type}")

    final_json = json.dumps(config_dict, indent=4)  # Pretty print with indentation

    print(final_json)
    return final_json
