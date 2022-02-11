from pyteal.ast.acct import AccountParam
from pyteal.ast.app import AppParam, OnComplete
from pyteal.ast.assert_ import Assert
from pyteal.ast.bytes import Bytes
from pyteal.ast.expr import Expr
from pyteal.ast.gitxn import Gitxn
from pyteal.ast.global_ import Global
from pyteal.ast.if_ import If
from pyteal.ast.int import Int
from pyteal.ast.itxn import InnerTxn, InnerTxnBuilder
from pyteal.ast.naryexpr import Concat
from pyteal.ast.seq import Seq
from pyteal.ast.txn import Txn, TxnField, TxnType
from pyteal.ast.unaryexpr import Btoi, Itob, Log, Sha512_256
from ..setup import MIN_BALANCE


def recursiveReplicator() -> Expr:
    return Seq(
        approval_prog := AppParam.approvalProgram(Global.current_application_id()),
        clear_state_prog := AppParam.clearStateProgram(Global.current_application_id()),
        current_balance := AccountParam.balance(Global.current_application_address()),
        Assert(approval_prog.hasValue()),
        Assert(clear_state_prog.hasValue()),
        Assert(current_balance.hasValue()),
        Log(Itob(Global.opcode_budget())),
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
