#!/usr/bin/env python
###############################################################################
#
#
# Project:  EPSG params finder
# Purpose:  Script to finde the relative epsg from input (code / title / param)
#	    from input (code / title / param)
#
# Author:   Massimo Di Stefano , massimodisasha@yahoo.it
#
###############################################################################
# Copyright (c) 2009, Massimo Di Stefano <massimodisasha@yahoo.it>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################
from __future__ import print_function
__author__ = "Massimo Di Stefano"
__copyright__ = "Copyright 2009, gfoss.it"
__credits__ = [""]
__license__ = "GPL V3"
__version__ = "1.0.0"
__maintainer__ = "Massimo Di Stefano"
__email__ = "epiesasha@me.com"
__status__ = "Production"
__date__ = ""

import sys
import os


apppath = os.path.abspath(os.path.dirname(sys.argv[0]))
#epsgpath='/add_here_the_path_to_the_epsg_file/'
epsgpath = str(apppath) + '/epsg'


def repc(s):
    s = s.replace('+', '')
    s = s.replace('>', '')
    s = s.replace('<', '')
    a = s.split(' ')
    code = a[0]
    a = a[1:-2]
    for i in range(0, len(a)):
        i = a[i]
    return code, a


def rept(s):
    s = s.replace('#', '')
    s = s.replace(' ', '_')
    s = s.replace('/', '-')
    s = s.replace('\n', '')
    s = s[1:]
    s = s.replace('_', ' ')
    return s


def rep3(t, o, p, out):
    f = open(str(t), 'r')
    f.seek(0)
    bighash = dict()
    for line in f:
        if line[0] == '#':
            title = rept(line)
        elif line[0] == '<':
            lista = repc(line)
            code = lista[0]
            param = lista[1]
            store = dict()
            for i in range(0, len(param)):
                par = param[i]
                par = par.split("=")
                a = par[0]
                if len(par) > 1:
                    store[a] = par[1]
                elif len(par) == 1:
                    store[a] = par[0]
            store['title'] = title
            store['code'] = code
            store['param'] = param
            if o == 'title':
                bighash[title] = store
            if o == 'code':
                bighash[code] = store
            if o == 'param':
                bighash[str(param)] = store
    sc = bighash[p]
    par = sc['param']
    cod = sc['code']
    tit = sc['title']
    #print(sc)
    if out == 'a':
        return par, cod, tit
    if out == 'c':
        return cod
    if out == 't':
        return tit
    if out == 'p':
        return par


def guioption(t, p):
    f = open(str(t), 'r')
    f.seek(0)
    bighash_code = dict()
    bighash_param = dict()
    bighash_title = dict()
    for line in f:
        if line[0] == '#':
            title = rept(line)
        elif line[0] == '<':
            lista = repc(line)
            code = lista[0]
            param = lista[1]
            store = dict()
            for i in range(0, len(param)):
                par = param[i]
                par = par.split("=")
                a = par[0]
                if len(par) > 1:
                    store[a] = par[1]
                elif len(par) == 1:
                    store[a] = par[0]
            store['title'] = title
            store['code'] = code
            store['param'] = param
            bighash_title[title] = store
            bighash_param[str(param)] = store
            bighash_code[code] = store
    if p == 'title':
        return bighash_title.keys()
    if p == 'code':
        return bighash_code.keys()
    if p == 'param':
        return bighash_param.keys()


def test():
    examples = '''
    examples :
    rep3('path to epsg','order',str('order'),'a')
    order (code,param,title)
    #'c' epsg code
    #'t' title
    # 'p' parameters
    # 'a' all

    # input : epsg code
    # output param, code, title

    >>>output = rep3(epsgpath,'code',str('4326'),'a')
    >>>print output
    '''
    print(examples)
    output = rep3(epsgpath, 'code', str('4326'), 'a')
    print(output)
    examples = '''
    # input :  title
    # output param, code, title

    >>>output = rep3(epsgpath,'title',str('WGS 84'),'a')
    >>>print output
    '''
    print(examples)
    output = rep3(epsgpath, 'title', str('WGS 84'), 'a')
    print (output)
    examples = '''
    # input :  param
    # output param, code, title

    >>>output = rep3(epsgpath,'param',str(['proj=longlat', 'ellps=WGS84', 'datum=WGS84', 'no_defs']),'a')
    >>>print output
    '''
    print(examples)
    output = rep3(epsgpath, 'param', str(['proj=longlat', 'ellps=WGS84', 'datum=WGS84', 'no_defs']), 'a')
    print(output)
    examples = '''
    # input :  param
    # output code

    >>>output = rep3(epsgpath,'param',str(['proj=tmerc', 'lat_0=0', 'lon_0=15', 'k=0.9996', 'x_0=2520000', 'y_0=0', 'ellps=intl', 'units=m', 'no_defs']),'c')
    >>>print output
    '''
    print(examples)
    output = rep3(epsgpath, 'param', str(
        ['proj=tmerc', 'lat_0=0', 'lon_0=15', 'k=0.9996', 'x_0=2520000', 'y_0=0', 'ellps=intl', 'units=m', 'no_defs']),
                  'c')
    print(output)


def Usage():
    print("Script to find the relative epsg from input : (code / title / param) and output : (code / title / param)")
    print("Usage in python :")
    print("")
    print("from episg import *")
    print("rep3('path to epsg','order',str('order'),'opt')")
    print("")
    print("order = code, title, param")
    print("str('order') = str('...')")
    print("opt = t (print title), p (print parameters), c (print epsg code), a (print all)")
    print("")
    print("example for the epsg code = 4326 :")
    print("rep3(epsgpath,'param',str(['proj=tmerc', 'lat_0=0', 'lon_0=15', 'k=0.9996', 'x_0=2520000', 'y_0=0', 'ellps=intl', 'units=m', 'no_defs']),'c')")
    print("print out the code :  4326")
    print("")
    print("Usage in bash :")
    print("python episg.py /Users/tiamo/Desktop/epsg code 3004 t")
    print("print out :  Monte Mario - Italy zone 2")


if __name__ == '__main__':
    i = 1
    t = None
    o = None
    p = None
    out = None
    while i < len(sys.argv):
        arg = sys.argv[i]
        if t is None:
            t = arg
        elif o is None:
            o = arg
        elif p is None:
            p = arg
        elif out is None:
            out = arg
        i = i + 1
    rep3(t, o, p, out)