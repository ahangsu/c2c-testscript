import base64
from algosdk.future.transaction import *
from . import get_approval, get_clear
from ..utils import TESTENV_INUSE


def some_func():
    get_approval()
    pass


if __name__ == "__main__":
    some_func()
