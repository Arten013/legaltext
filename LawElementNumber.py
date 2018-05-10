from decimal import Decimal
from xml.etree.ElementTree import Element
import re
from LawError import *
from EType import ETYPES_DICT

class LawElementNumber(object):
    def __init__(self, etype, arg):
        self.etype = etype
        if isinstance(arg, (int, str)):
            self.num = Decimal(arg)     
        elif isinstance(arg, (Decimal,)):
            self.num = arg
        elif isinstance(arg, (LawElementNumber,)):
            self.num = arg.num
        elif isinstance(arg, (Element,)):
            self.num = self.from_etree(arg)
        else:
            raise TypeError("Invalid type for init LawElementNumber: {}".format(arg.__class__.__name__))

    def __float__(self):
        return float(self.num)

    def __str__(self):
        try:
            return self._str
        except:
            pass
        self._str = "第" + str(self.num.quantize(Decimal('1'))) + ETYPES_DICT[self.etype]
        num = self.num - self.num.quantize(Decimal('1'))
        while num.quantize(Decimal('1')) != Decimal(0):
            self.num *= 100
            self._str += "の"+str(num.quantize(Decimal('1')))
            num = num - num.quantize(Decimal('1'))
        return self._str

    def from_etree(self, etree):
        try:
            strnum = etree.attrib['Num']
        except KeyError:
            return Decimal(0)
        if re.match("^[0-9]+(?:_[0-9]+)*$", strnum) is None:
            raise LawElementNumberError(error_detail="Invalid Format {}".format(strnum))
        num = Decimal(0)
        mul = Decimal(1)
        for n in strnum.split("_"):
            num += Decimal(n) * mul
            mul /= Decimal(1000)
        return num