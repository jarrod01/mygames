import itertools
for i in itertools.permutations(map(str, range(10)), 4):
    if int('{0}{1}{0}'.format(i[2], i[3])) + int(''.join(i[:3])) == int(''.join(i)):
        print('YAO:{}, ZUO:{}, HAO:{}, SHI:{}'.format(*i))
        break


import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {'packages': [], 'excludes': []}

setup(  name = '<程序名>',
        version = '<程序版本>',
        description = '<程序描述>',
        options = {'build_exe': build_exe_options},
        executables = [Executable('main.py')])