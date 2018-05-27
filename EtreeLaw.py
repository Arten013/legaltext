import xml.etree.ElementTree as ET
import re
import traceback
import threading
import os
from pprint import pprint
from collections import Counter
import asyncio
import concurrent.futures 

from LawError import *
from EtreeLawElement import *
from multiprocessing import Pool
from LawAbstCls import LawAbstCls

def get_text(b, e_val):
    if b is not None and len(b.text) > 0:
        return b.text
    else:
        return e_val

class EtreeLaw(LawAbstCls):
    @property
    def identifier(self):
        return int(re.sub("/", "", self.code[2:]))

    def set(self, path):
        self.path = path

    def _path_to_code(self):
        p, file = os.path.split(self.path)
        self.file_code = os.path.splitext(file)[0]
        p, self.municipality_code = os.path.split(p)
        _, self.prefecture_code = os.path.split(p)

    def _reg_metadata(self, root):
        self._name = root.get_law_name()
        self._num = root.get_law_num()

    def load(self, path=None):
        self.path = os.path.abspath(self.path if path is None else path)
        print(self.path)
        self._path_to_code()
        try:
            root_etree = ET.parse(self.path).getroot()
            root = Root(self)
            root.inheritance(root_etree)
            if self._name is None or self._num is None:
                self._reg_metadata(root)
            return root
        except:
            print(traceback.format_exc())
            raise XMLStructureError(self)

    async def async_load(self, path=None):
        self.path = os.path.abspath(self.path if path is None else path)
        print(self.path)
        self._path_to_code()
        try:
            with concurrent.futures.ThreadPoolExecutor(1) as e:
                et = await asyncio.get_event_loop().run_in_executor(e, ET.parse, path)
            root_etree = et.getroot()
            root = Root(self)
            root.inheritance(root_etree)
            if self._name is None or self._num is None:
                self._reg_metadata(root)
            return root
        except:
            print(traceback.format_exc())
            raise XMLStructureError(self)

if __name__ == '__main__':
    ld = EtreeLaw()
    ld.load("testset/01/000001/0001.xml")
    for s in ld.iter_sentences():
        print(s)
