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
def encodeStrToABIStr(pyStr: Expr):
    return Concat(Extract(Itob(Len(pyStr)), Int(6), Int(2)), pyStr)


retPrefix = Bytes("base16", "151f7c75")


@Subroutine(TealType.none)
def TealMethodReturn(value):
    return Log(Concat(retPrefix, encodeStrToABIStr(value)))
