import os


def load_env_file(env_file):
    env_values = {}

    if not env_file.exists():
        return env_values

    with open(env_file, encoding="utf-8") as file_handle:
        for raw_line in file_handle:
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            env_values[key.strip()] = value.strip()

    return env_values


def get_config_value(name, env_values):
    return os.environ.get(name) or env_values.get(name)
