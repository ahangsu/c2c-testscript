from ..utils import TealItoa, TealMethodReturn
from pyteal import *


@Subroutine(TealType.uint64, name="echo(uint64)string")
def echo():
    return Seq(
        TealMethodReturn(
            Concat(
                Bytes("In app id "),
                TealItoa(Txn.application_id()),
                Bytes(" which was called by app id "),
                TealItoa(Global.caller_app_id()),
            )
        ),
        Int(1),
    )


@Subroutine(TealType.uint64, name="callecho(application)string")
def callecho():
    calledAppId = Btoi(Txn.application_args[1])
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: Txn.applications[calledAppId],
                TxnField.application_args: [MethodSignature(echo.name())],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
        Log(InnerTxn.logs[0]),
        Int(1),
    )


APPROVAL = Cond(
    [Txn.application_id() == Int(0), Approve()],
    [
        Or(
            Txn.on_completion() == OnComplete.UpdateApplication,
            Txn.on_completion() == OnComplete.DeleteApplication,
        ),
        Return(Txn.sender() == Global.creator_address()),
    ],
    [
        Or(
            Txn.on_completion() == OnComplete.CloseOut,
            Txn.on_completion() == OnComplete.OptIn,
        ),
        Approve(),
    ],
    [Txn.application_args[0] == MethodSignature(echo.name()), Return(echo())],
    [
        Txn.application_args[0] == MethodSignature(callecho.name()),
        Return(callecho()),
    ],
)


CLEAR = Approve()


def get_approval():
    return compileTeal(APPROVAL, mode=Mode.Application, version=6)


def get_clear():
    return compileTeal(CLEAR, mode=Mode.Application, version=6)
