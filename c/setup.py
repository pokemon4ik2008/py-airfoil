from distutils.core import setup, Extension

module1 = Extension('optimised',
                    include_dirs = ['/home/paulj/projects/Python-2.6.6/Include'],
                    sources = ['optimised.c'])

setup (name = 'PackageName',
       version = '1.0',
       description = 'This is a demo package',
       ext_modules = [module1])
