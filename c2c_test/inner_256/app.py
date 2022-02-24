from c2c_test.utils import MAX_INNER_CALL_COUNT
from ..utils import TealItoa
from pyteal import *


@Subroutine(TealType.uint64)
def echo():
    return Seq(
        Log(
            Concat(
                TealItoa(App.globalGet(Bytes("counter"))),
                Bytes(" time(s) called, called by "),
                TealItoa(Global.caller_app_id()),
            )
        ),
        App.globalPut(Bytes("counter"), App.globalGet(Bytes("counter")) + Int(1)),
        Int(1),
    )


@Subroutine(TealType.uint64)
def callecho():
    max_txn_num = MAX_INNER_CALL_COUNT
    iter_index = ScratchVar()
    init_cond = iter_index.store(Int(0))
    end_cond = iter_index.load() < Int(max_txn_num)
    iter_trans = iter_index.store(iter_index.load() + Int(1))

    return Seq(
        For(init_cond, end_cond, iter_trans).Do(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.ApplicationCall,
                        TxnField.application_id: Txn.applications[1],
                        TxnField.fee: Int(0),
                    }
                ),
                InnerTxnBuilder.Submit(),
            )
        ),
        Int(1),
    )


DEFAULT_BRANCHES = [
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
]


APPROVAL_ECHO = Cond(
    [
        Txn.application_id() == Int(0),
        Seq(App.globalPut(Bytes("counter"), Int(0)), Approve()),
    ],
    *DEFAULT_BRANCHES,
    [Txn.on_completion() == OnComplete.NoOp, Return(echo())],
)


APPROVAL_CALL = Cond(
    [Txn.application_id() == Int(0), Approve()],
    *DEFAULT_BRANCHES,
    [
        Txn.on_completion() == OnComplete.NoOp,
        Return(callecho()),
    ],
)


CLEAR = Approve()


def get_approval_call():
    return compileTeal(APPROVAL_CALL, mode=Mode.Application, version=6)


def get_approval_echo():
    return compileTeal(APPROVAL_ECHO, mode=Mode.Application, version=6)


def get_clear():
    return compileTeal(CLEAR, mode=Mode.Application, version=6)
