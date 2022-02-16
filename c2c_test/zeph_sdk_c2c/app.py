from pyteal import *
from ..utils import *


@Subroutine(TealType.uint64, name="randInt(uint64)(uint64,byte[17])")
def randInt() -> Expr:
    return Seq()


@Subroutine(TealType.uint64, name="randElement(string,application)(byte,byte[17])")
def randElement() -> Expr:
    return Seq()


@Subroutine(TealType.uint64, name="setReels(string,string,string)void")
def setReels() -> Expr:
    return Seq()


@Subroutine(
    TealType.uint64,
    name="spin(application,application)(byte[3],byte[17],byte[17],byte[17])",
)
def spin() -> Expr:
    return Seq()


FAKE_RANDOM_APPROVAL = Cond([])


RANDOM_BYTE_APPROVAL = Cond([])


SLOT_MACHINE_APPROVAL = Cond([])


CLEARSTATE = Approve()


def get_fake_random_approval():
    return compileTeal(FAKE_RANDOM_APPROVAL, mode=Mode.Application, version=6)


def get_random_byte_approval():
    return compileTeal(RANDOM_BYTE_APPROVAL, mode=Mode.Application, version=6)


def get_slot_machine_approval():
    return compileTeal(SLOT_MACHINE_APPROVAL, mode=Mode.Application, version=6)


def get_clear():
    return compileTeal(CLEARSTATE, mode=Mode.Application, version=6)
