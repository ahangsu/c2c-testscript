from pyteal import *
from ..utils import TealItoa


@Subroutine(TealType.uint64)
def log_caller():
    return Seq(
        Log(
            Concat(
                Bytes("called by "),
                TealItoa(Global.caller_app_id()),
            )
        ),
        Int(1),
    )


@Subroutine(TealType.uint64)
def call_someone():
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: Txn.applications[1],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
        Int(1),
    )


DEFAULT_BARNCHES = [
    [
        Or(
            Txn.on_completion() == OnComplete.UpdateApplication,
            Txn.on_completion() == OnComplete.DeleteApplication,
            Txn.on_completion() == OnComplete.CloseOut,
            Txn.on_completion() == OnComplete.OptIn,
        ),
        Approve(),
    ],
]

APPROVAL = Cond(
    [Txn.application_id() == Int(0), Approve()],
    *DEFAULT_BARNCHES,
    [Txn.application_args.length() > Int(0), Return(call_someone())],
    [Txn.on_completion() == OnComplete.NoOp, Return(log_caller())]
)


CLEAR = Approve()


def get_approval():
    return compileTeal(APPROVAL, mode=Mode.Application, version=6)


def get_clear():
    return compileTeal(CLEAR, mode=Mode.Application, version=6)
