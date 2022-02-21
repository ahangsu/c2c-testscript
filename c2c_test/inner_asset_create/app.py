from pyteal import *
from ..utils import *


@Subroutine(TealType.uint64)
def create_plata_plomo():
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_total: Int(100000),
                TxnField.config_asset_decimals: Int(3),
                TxnField.config_asset_unit_name: Bytes("oz"),
                TxnField.config_asset_name: Bytes("plata"),
                TxnField.config_asset_manager: Global.current_application_address(),
                TxnField.config_asset_reserve: Global.current_application_address(),
                TxnField.config_asset_freeze: Global.current_application_address(),
                TxnField.config_asset_clawback: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_total: Int(1000000),
                TxnField.config_asset_decimals: Int(3),
                TxnField.config_asset_unit_name: Bytes("oz"),
                TxnField.config_asset_name: Bytes("plomo"),
                TxnField.config_asset_manager: Global.current_application_address(),
                TxnField.config_asset_reserve: Global.current_application_address(),
                TxnField.config_asset_freeze: Global.current_application_address(),
                TxnField.config_asset_clawback: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Submit(),
        Int(1),
    )


@Subroutine(TealType.uint64)
def create_oro_cobre():
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_total: Int(1000),
                TxnField.config_asset_decimals: Int(3),
                TxnField.config_asset_unit_name: Bytes("oz"),
                TxnField.config_asset_name: Bytes("oro"),
                TxnField.config_asset_manager: Global.current_application_address(),
                TxnField.config_asset_reserve: Global.current_application_address(),
                TxnField.config_asset_freeze: Global.current_application_address(),
                TxnField.config_asset_clawback: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_total: Int(1000000),
                TxnField.config_asset_decimals: Int(3),
                TxnField.config_asset_unit_name: Bytes("oz"),
                TxnField.config_asset_name: Bytes("cobre"),
                TxnField.config_asset_manager: Global.current_application_address(),
                TxnField.config_asset_reserve: Global.current_application_address(),
                TxnField.config_asset_freeze: Global.current_application_address(),
                TxnField.config_asset_clawback: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Submit(),
        Int(1),
    )


@Subroutine(TealType.uint64)
def top_level():
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: Txn.applications[1],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: Txn.applications[2],
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
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


PLATA_PLOMO_APPROVAL = Cond(
    [Txn.application_id() == Int(0), Approve()],
    *DEFAULT_HANDLERS,
    [Txn.on_completion() == OnComplete.NoOp, Return(create_plata_plomo())]
)


ORO_COBRE_APPROVAL = Cond(
    [Txn.application_id() == Int(0), Approve()],
    *DEFAULT_HANDLERS,
    [Txn.on_completion() == OnComplete.NoOp, Return(create_oro_cobre())]
)


TOP_LEVEL_APPROVAL = Cond(
    [Txn.application_id() == Int(0), Approve()],
    *DEFAULT_HANDLERS,
    [Txn.on_completion() == OnComplete.NoOp, Return(top_level())]
)


CLEARSTATE = Approve()


def get_plata_plomo_approval():
    return compileTeal(PLATA_PLOMO_APPROVAL, mode=Mode.Application, version=6)


def get_oro_cobre_approval():
    return compileTeal(ORO_COBRE_APPROVAL, mode=Mode.Application, version=6)


def get_top_level():
    return compileTeal(TOP_LEVEL_APPROVAL, mode=Mode.Application, version=6)


def get_clear():
    return compileTeal(CLEARSTATE, mode=Mode.Application, version=6)
