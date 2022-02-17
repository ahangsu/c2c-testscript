from pyteal import *
from ..utils import *


@Subroutine(TealType.uint64, name="randInt(uint64)(uint64,byte[17])")
def randInt() -> Expr:
    proof_string = Concat(
        Itob(Global.round()),
        Bytes("#"),
        Itob(App.globalGet(Bytes("counter"))),
    )
    return Seq(
        TealMethodReturn(
            Concat(
                Itob(
                    Mod(
                        ExtractUint64(
                            Sha512_256(proof_string),
                            Int(0),
                        ),
                        Btoi(Txn.application_args[1]),
                    )
                ),
                proof_string,
            )
        ),
        App.globalPut(Bytes("counter"), App.globalGet(Bytes("counter")) + Int(1)),
        Int(1),
    )


@Subroutine(TealType.uint64, name="randElement(string,application)(byte,byte[17])")
def randElement() -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: Txn.applications[
                    Btoi(Txn.application_args[1])
                ],
                TxnField.application_args: [
                    MethodSignature(randInt.name()),
                    Itob(Btoi(Txn.application_args[1]) - Int(2)),
                ],
            }
        ),
        InnerTxnBuilder.Submit(),
        Assert(InnerTxn.logs.length() == Int(1)),
        TealMethodReturn(
            Concat(
                Extract(
                    Suffix(Txn.application_args[1], Int(2)),
                    Btoi(Extract(InnerTxn.logs[0], Int(4), Int(8))),
                    Int(1),
                ),
                Suffix(InnerTxn.logs[0], Int(12)),
            )
        ),
        Int(1),
    )


@Subroutine(TealType.uint64, name="setReels(string,string,string)void")
def setReels() -> Expr:
    return Seq(
        App.globalPut(Bytes("reel2"), Suffix(Txn.application_args[1], Int(2))),
        App.globalPut(Bytes("reel1"), Suffix(Txn.application_args[2], Int(2))),
        App.globalPut(Bytes("reel0"), Suffix(Txn.application_args[3], Int(2))),
        Int(1),
    )


@Subroutine(
    TealType.uint64,
    name="spin(application,application)(byte[3],byte[17],byte[17],byte[17])",
)
def spin() -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: Txn.applications[2],
                TxnField.application_args: [
                    MethodSignature(randElement.name()),
                    encodeStrToABIStr(App.globalGet(Bytes("reel2"))),
                ],
                TxnField.applications: [Txn.applications[1]],
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: Txn.applications[2],
                TxnField.application_args: [
                    MethodSignature(randElement.name()),
                    encodeStrToABIStr(App.globalGet(Bytes("reel1"))),
                ],
                TxnField.applications: [Txn.applications[1]],
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: Txn.applications[2],
                TxnField.application_args: [
                    MethodSignature(randElement.name()),
                    encodeStrToABIStr(App.globalGet(Bytes("reel0"))),
                ],
                TxnField.applications: [Txn.applications[1]],
            }
        ),
        InnerTxnBuilder.Submit(),
        TealMethodReturn(
            Concat(
                Extract(Gitxn[0].logs[0], Int(4), Int(1)),
                Extract(Gitxn[1].logs[0], Int(4), Int(1)),
                Extract(Gitxn[2].logs[0], Int(4), Int(1)),
                Suffix(Gitxn[0].logs[0], Int(5)),
                Suffix(Gitxn[1].logs[0], Int(5)),
                Suffix(Gitxn[2].logs[0], Int(5)),
            )
        ),
        Int(1),
    )


DEFAULT_HANDLERS = [
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


FAKE_RANDOM_APPROVAL = Cond(
    [
        Txn.application_id() == Int(0),
        Seq(App.globalPut(Bytes("counter"), Int(0)), Approve()),
    ],
    *DEFAULT_HANDLERS,
    [Txn.application_args[0] == MethodSignature(randInt.name()), Return(randInt())],
)


RANDOM_BYTE_APPROVAL = Cond(
    [Txn.application_id() == Int(0), Approve()],
    *DEFAULT_HANDLERS,
    [
        Txn.application_args[0] == MethodSignature(randElement.name()),
        Return(randElement()),
    ],
)


SLOT_MACHINE_APPROVAL = Cond(
    [
        Txn.application_id() == Int(0),
        Seq(
            App.globalPut(Bytes("reel0"), Bytes("@!-")),
            App.globalPut(Bytes("reel1"), Bytes("@@!---")),
            App.globalPut(Bytes("reel2"), Bytes("@!------")),
            Approve(),
        ),
    ],
    *DEFAULT_HANDLERS,
    [Txn.application_args[0] == MethodSignature(setReels.name()), Return(setReels())],
    [Txn.application_args[0] == MethodSignature(spin.name()), Return(spin())],
)


CLEARSTATE = Approve()


def get_fake_random_approval():
    return compileTeal(FAKE_RANDOM_APPROVAL, mode=Mode.Application, version=6)


def get_random_byte_approval():
    return compileTeal(RANDOM_BYTE_APPROVAL, mode=Mode.Application, version=6)


def get_slot_machine_approval():
    return compileTeal(SLOT_MACHINE_APPROVAL, mode=Mode.Application, version=6)


def get_clear():
    return compileTeal(CLEARSTATE, mode=Mode.Application, version=6)
