
import dawgie

class Container(dawgie.Aspect):
    def __init__(self, l1=None, l2=None, parent:Container=None):
        self.__l1 = l1
        self.__l2 = l2
        self.__parent = parent if parent else self
        return

    def __contains__(self, item): return item in self.keys()

    def __getitem__(self, key):
        # pylint: disable=protected-access
        if self.__l1 is None:
            result = Container(key, self.__l2, self.__parent)
        elif self.__l2 is None:
            result = Container(self.__l1, key, self.__parent)
        else: result = self.__parent._fill_item (self.__l1, self.__l2, key)
        return result

    def __iter__(self):
        # pylint: disable=protected-access
        for k in self.__parent._keys (self.__l1, self.__l2): yield k
        return

    def __len__(self): return len ([k for k in self])

    def _ckeys (self, l1k, l2k): raise NotImplementedError()
    def _fill_item (self, l1k, l2k, l3k): raise NotImplementedError()

    def items(self):
        '''genrator of current (key,value) pairs'''
        for i in zip (self.keys(), self.values()): yield i
        return

    def keys(self):
        '''generator of current level of keys'''
        for k in self: yield k
        return

    def values(self):
        '''generator of current level of values'''
        for k in self.keys(): yield self[k]
        return
    pass
