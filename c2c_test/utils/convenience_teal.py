from pyteal import *


@Subroutine(TealType.bytes)
def TealIntToAscii(arg):
    return Extract(Bytes("0123456789"), arg, Int(1))


@Subroutine(TealType.bytes)
def TealItoa(i):
    return If(
        i == Int(0),
        Bytes("0"),
        Concat(
            If(i / Int(10) > Int(0), TealItoa(i / Int(10)), Bytes("")),
            TealIntToAscii(i % Int(10)),
        ),
    )


@Subroutine(TealType.bytes)
def encodeStrToABIStr(tealByteStr: Expr):
    return Concat(Extract(Itob(Len(tealByteStr)), Int(6), Int(2)), tealByteStr)


retPrefix = Bytes("base16", "151f7c75")


@Subroutine(TealType.none)
def TealMethodReturn(value):
    return Log(Concat(retPrefix, encodeStrToABIStr(value)))


# Wilco!
# pragma version 6; int 1
VER6_JUST_APPROVAL = Bytes("base16", "068101")
