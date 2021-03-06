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
    def load_from_path(self, path):
        assert self.root is None
        p = os.path.abspath(path)
        p, file = os.path.split(p)
        self.file_code = os.path.splitext(file)[0]
        p, self.municipality_code = os.path.split(p)
        _, self.prefecture_code = os.path.split(p)
        try:
            self.root_etree = ET.parse(path).getroot()
            root = Root(self)
            root.inheritance(self.root_etree)
            self.root = root
        except:
            print(traceback.format_exc())
            raise XMLStructureError(self)

    async def async_load_from_path(self, path):
        assert self.root is None
        p = os.path.abspath(path)
        p, file = os.path.split(p)
        self.file_code = os.path.splitext(file)[0]
        p, self.municipality_code = os.path.split(p)
        _, self.prefecture_code = os.path.split(p)
        try:
            with concurrent.futures.ThreadPoolExecutor(1) as e:
                et = await asyncio.get_event_loop().run_in_executor(e, ET.parse, path)
            self.root_etree = et.getroot()
            root = Root(self)
            root.inheritance(self.root_etree)
            self.root = root
        except:
            print(traceback.format_exc())
            raise XMLStructureError(self)
        return self

if __name__ == '__main__':
    ld = EtreeLaw()
    ld.load_from_path("testset/01/000001/0001.xml")
    for s in ld.iter_sentences():
        print(s)
