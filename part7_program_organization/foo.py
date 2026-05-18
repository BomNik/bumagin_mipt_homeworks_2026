# import sys


sys = ...

# https://github.com/dabeaz-course/practical-python/blob/master/Notes/03_Program_organization/01_Script.md

"""
typedef struct {
    PyObject ob_base;
    PyObject *md_dict;
    struct PyModuleDef *md_def;
    void *md_state;
    PyObject *md_weaklist;
    PyObject *md_name;
} PyModuleObject;
"""

from types import ModuleType


"""
Built-in modules (C modules).
Frozen modules. (marshaled python executable files) https://docs.python.org/3/library/marshal.html
C extensions. .so
Python source code files (.py files).
Python bytecode files (.pyc files).
Directories.
"""

"""
mylibs/
    company_name/
        package1/...

morelibs/
    company_name/
        package1/...
        package2/...
"""


# import company_name.package1


"""
company_name.__path__
_NamespacePath(["/morelibs/company_name", "/mylibs/company_name"])
"""


from sys import path
from os import chdir


# from module import func, MyClass, submodule


# func = module.func
# MyClass = module.MyClass
# submodule = module.submodule


# del module


# from module.submodule.subsubmodule import Class


from . import program
# from .. import part4_oop
# from .program import d
# from ..part4_oop import hw45


__package__


"""
case TARGET(IMPORT_NAME): {
    PyObject *name = GETITEM(names, oparg);
    PyObject *fromlist = POP();
    PyObject *level = TOP();
    PyObject *res;
    res = import_name(tstate, f, name, fromlist, level);
    Py_DECREF(level);
    Py_DECREF(fromlist);
    SET_TOP(res);
    if (res == NULL)
        goto error;
    DISPATCH();
}
"""


"import m -> m = __import__('m', globals(), locals(), None, 0)"


"https://tenthousandmeters.com/blog/python-behind-the-scenes-11-how-the-python-import-system-works/"


if __name__ == "__main__":
    ...

# Если `python foo.py` - __name__ это __main__
# Если import foo - __name__ это foo
