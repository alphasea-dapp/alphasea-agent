import stringcase


def convert_keys_to_snake_case(x: dict):
    return { stringcase.snakecase(key): x[key] for key in x }
