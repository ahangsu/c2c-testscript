from pyteal import *
from ..utils import MIN_BALANCE


def recursiveReplicator() -> Expr:
    return Seq(
        approval_prog := AppParam.approvalProgram(Global.current_application_id()),
        clear_state_prog := AppParam.clearStateProgram(Global.current_application_id()),
        current_balance := AccountParam.balance(Global.current_application_address()),
        Assert(approval_prog.hasValue()),
        Assert(clear_state_prog.hasValue()),
        Assert(current_balance.hasValue()),
        Log(Itob(Exp(Int(2), Btoi(Txn.application_args[0])))),
        If(Btoi(Txn.application_args[0]) > Int(0)).Then(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.ApplicationCall,
                        TxnField.fee: Int(0),
                        TxnField.approval_program: approval_prog.value(),
                        TxnField.clear_state_program: clear_state_prog.value(),
                    }
                ),
                InnerTxnBuilder.Submit(),
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.fee: Int(0),
                        TxnField.amount: current_balance.value() - Int(MIN_BALANCE),
                        TxnField.receiver: Sha512_256(
                            Concat(
                                Bytes("appID"), Itob(Gitxn[0].created_application_id())
                            )
                        ),
                    }
                ),
                InnerTxnBuilder.Next(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.ApplicationCall,
                        TxnField.application_args: [
                            Itob(Btoi(Txn.application_args[0]) - Int(1))
                        ],
                        TxnField.application_id: InnerTxn.created_application_id(),
                        TxnField.fee: Int(0),
                        TxnField.on_completion: OnComplete.DeleteApplication,
                    }
                ),
                InnerTxnBuilder.Submit(),
            )
        ),
        Int(1),
    )


APPROVAL = (
    If(Txn.application_id() == Int(0))
    .Then(Approve())
    .ElseIf(Txn.application_args.length() == Int(1))
    .Then(Return(recursiveReplicator()))
    .Else(Reject())  # This will never happen
)


CLEARSTATE = Approve()


def get_approval():
    return compileTeal(APPROVAL, mode=Mode.Application, version=6)


def get_clear():
    return compileTeal(CLEARSTATE, mode=Mode.Application, version=6)
