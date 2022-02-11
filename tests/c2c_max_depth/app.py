from pyteal import *


recursive_replicator = Seq(
    If(Btoi(Txn.application_args[0] > Int(0)))
    .Then(
        Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.ApplicationCall,
            }),
            InnerTxnBuilder.Submit(),
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.Next(),
            InnerTxnBuilder.Submit(),
        )
    ),
    Int(1)
)
