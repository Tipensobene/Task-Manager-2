import logging
from pathlib import Path
from functools import wraps


BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE=LOG_DIR/"tasks_manager.log"

LOG_DIR.mkdir(
            parents=True,
            exist_ok=True
)
logging.basicConfig(filename=LOG_FILE,
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    encoding="utf-8"
                    )


def get_valid_int(prompt: str) -> int:
    while True:
        try:
            cur_id = int(input(prompt))
            return cur_id

        except ValueError:
            print("请输入合法整数！")



def log_operation(operation_name):

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result=func(*args, **kwargs)

            logging.info(f"{operation_name}: {result.title}")

            return result

        return wrapper

    return decorator



