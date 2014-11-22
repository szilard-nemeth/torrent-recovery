__author__ = 'szyszy'

from collections import defaultdict
import os
import random
from mock import PropertyMock

class Tree(defaultdict):
    def __init__(self, value=None):
        super(Tree, self).__init__(Tree)
        self.value = []
        self.size_override_for_files = 0

class MockFs:
    def __init__(self, add_defaults=True):
        self.root = Tree()
        self.last_dir = self.root
        self.last_sizes_dict = None
        self.possible_sizes = [12345, 34567, 897654, 67565, 999999]
        self.make_path_as_sizes_dict_element = MockFs.make_path_full_path
        if add_defaults:
            self.add_defaults()

    def add_dir(self, dir):
        if not self.last_dir[dir]:
            self.last_dir[dir] = Tree()

        self.last_dir = self.last_dir[dir]
        return self

    def add_files(self, files):
        if not self.last_dir.value:
            self.last_dir.value = files
        return self

    def end(self, size=0):
        #add size override for all files in last dir
        if size > 0:
            self.last_dir.size_override_for_files = size
        self.last_dir = self.root

    def add_defaults(self):
        self.add_dir('a').add_dir('d1').add_dir('d2').add_files(['a.d1.d2.f1', 'a.d1.d2.f2']).end()
        self.add_dir('a').add_dir('d1').add_files(['a.d1.f1']).end()
        self.add_dir('a').add_dir('d2').add_files(['a.d2.f1', 'a.d2.f2']).end()
        self.add_dir('a').add_dir('d3').add_files(['a.d3.f1', 'a.d3.f2', 'a.d3.f3']).end()
        self.add_dir('a').add_files(['a.f1', 'a.f2']).end()

        self.add_dir('b').add_dir('d1').add_files(['b.d1.f1', 'b.d1.d2']).end()
        self.add_dir('b').add_dir('d2').add_files(['b.d2.f1', 'b.d2.d2']).end()
        self.add_dir('b').add_dir('d3').add_files(['b.d3.f1', 'b.d3.f2', 'b.d3.f3']).end()
        self.add_dir('b').add_files(['b.f1', 'b.f2', 'b.f3', 'b.f4']).end()

    def get_top_level_dirs(self):
        return self.root.keys()

    def get_size_dict(self):
        def get_size_dict_internal(root_dir_name, sizes_dict):
            iter_map = Helper.get_subdict(self.root, root_dir_name)
            nondirs = iter_map.value
            if nondirs:
                for filename in nondirs:
                    if iter_map.size_override_for_files > 0:
                        size = iter_map.size_override_for_files
                    else:
                        size = random.choice(self.possible_sizes)
                    value = self.make_path_as_sizes_dict_element(root_dir_name, filename)
                    if size in sizes_dict:
                        sizes_dict[size].append(value)
                    else:
                        sizes_dict[size] = [value]

            dirs = []
            for k, v in iter_map.iteritems():
                if isinstance(v, dict):
                    dirs.append(k)

            for dir in dirs:
                get_size_dict_internal(os.path.join(root_dir_name, dir), sizes_dict)

        sizes_dict = {}
        for dir in self.get_top_level_dirs():
            get_size_dict_internal(dir, sizes_dict)
        return sizes_dict

    def get_last_sizes_dict(self):
        if not self.last_sizes_dict:
            self.last_sizes_dict = self.get_size_dict()
        return self.last_sizes_dict


    @classmethod
    def make_path_subdir_as_root(cls, root_dir_name, filename):
        return os.path.join(os.path.split(root_dir_name)[1], filename)

    @classmethod
    def make_path_full_path(cls, root_dir_name, filename):
        return os.path.join(root_dir_name, filename)



class Helper:
     #from: http://nicks-liquid-soapbox.blogspot.hu/2011/03/splitting-path-to-list-in-python.html
    @staticmethod
    def splitpath(path, maxdepth=20):
        (head, tail) = os.path.split(path)
        return Helper.splitpath(head, maxdepth - 1) + [tail] if maxdepth and head and head != path else [head or tail]

    @staticmethod
    def get_subdict(src_dict, fullpath):
            paths = Helper.splitpath(fullpath, 20)
            dict = src_dict
            for path in paths:
                dict = dict[path]
            return dict


class MockOs:

    @classmethod
    def init(cls, param_fs, mock_os):
        MockOs.fs = param_fs
        MockOs.mock_os = mock_os
        MockOs.walk_stack = []
        mock_os.walk.side_effect = MockOs.os_walk_side_effect
        mock_os.stat.side_effect = MockOs.os_stat_side_effect
        mock_os.path.join.side_effect = MockOs.os_path_join_side_effect
        mock_os.path.abspath.side_effect = MockOs.os_path_abspath_side_effect

    @staticmethod
    def os_walk_side_effect(*args, **kwargs):
        root_dir_name = args[0]
        #append the dir name if it's a root, delete the old root if needed
        if os.sep not in root_dir_name:
            if len(MockOs.walk_stack) == 1:
                MockOs.walk_stack.pop()
            MockOs.walk_stack.append(root_dir_name)
        iter_map = Helper.get_subdict(MockOs.fs.root, root_dir_name)
        nondirs = iter_map.value
        dirs = []
        for k, v in iter_map.iteritems():
            if isinstance(v, dict):
                dirs.append(k)
        yield os.path.split(root_dir_name)[1], dirs, nondirs

        for dir in dirs:
            MockOs.walk_stack.append(dir)
            for x in MockOs.os_walk_side_effect(os.path.join(root_dir_name, dir)):
                yield x
            #pop from the stack when iteration is finished for the current dir
            MockOs.walk_stack.pop()



    @staticmethod
    def os_stat_side_effect(*args, **kwargs):
        size_dict = MockOs.fs.get_last_sizes_dict()
        path = args[0]
        for size, paths in size_dict.iteritems():
            if path in paths:
                type(MockOs.mock_os.stat).st_size = PropertyMock(return_value=size)
                return MockOs.mock_os.stat
        # if none of the list contained the path, something is wrong with the test
        raise RuntimeError('Path ' + path + ' not found in the size_dict')

    @staticmethod
    def os_path_join_side_effect(*args, **kwargs):
        return os.path.join(*args, **kwargs)

    @staticmethod
    def os_path_abspath_side_effect(*args, **kwargs):
        if len(MockOs.walk_stack) == 0:
            return args[0]
        ##if we are on level 1, we can skip the base dir because args[0] contains it (base\filename)
        if len(MockOs.walk_stack) == 1:
            return args[0]
        ##if we are on level 1+n, we can skip the last part because args[0] contains it (base\filename)
        elif len(MockOs.walk_stack) >= 2:
            stack_size = len(MockOs.walk_stack)
            elements = MockOs.walk_stack[1:stack_size - 1]
            elements.append(args[0])
            return os.path.join(MockOs.walk_stack[0], *elements)

