def red(text: str) -> str:
    return f"\033[31m{text}\033[0m"

def green(text: str) -> str:
    return f"\033[32m{text}\033[0m"

def orange(text: str) -> str:
    return f"\033[33m{text}\033[0m"

def blue(text: str) -> str:
    return f"\033[34m{text}\033[0m"

def magenta(text: str) -> str:
    return f"\033[35m{text}\033[0m"

def cyan(text: str) -> str:
    return f"\033[36m{text}\033[0m"

def light_gray(text: str) -> str:
    return f"\033[37m{text}\033[0m"