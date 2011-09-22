# This is the version of this source code.

manual_verstr = "3.0"

auto_build_num = "127"

verstr = manual_verstr + "." + auto_build_num

from distutils.version import LooseVersion as distutils_Version
__version__ = distutils_Version(verstr)
