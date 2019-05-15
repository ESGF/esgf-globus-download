from __future__ import print_function
from setuptools import setup, find_packages
import glob
import subprocess
import os

Version = "1.0"
p = subprocess.Popen(
    ("git",
     "describe",
     "--tags"),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
try:
    descr = p.stdout.readlines()[0].decode("utf-8").strip()
    Version = "-".join(descr.split("-")[:-2])
    if Version == "":
        Version = descr
except Exception as err:
    print("Error:", err)
    descr = Version

p = subprocess.Popen(
    ("git",
     "log",
     "-n1",
     "--pretty=short"),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
try:
    commit = p.stdout.readlines()[0].split()[1]
except:
    commit = ""
f = open("esgf-globus-download/version.py", "w")
print("__version__ = '%s'" % Version, file=f)
print("__git_tag_describe__ = '%s'" % descr, file=f)
print("__git_sha1__ = '{}'".format(commit.decode("utf-8")), file=f)
f.close()


packages = find_packages()

scripts = ['esgf-globus-download/esgf-globus-download']


setup(name='esgf-globus-download',
      version=descr,
      author='ESGF',
      description='tools to search esgf and download via globus',
      url='http://github.com/ESGF/esgf-globus-download',
      packages=packages,
      scripts=scripts,
#      data_files=data_files
      )
