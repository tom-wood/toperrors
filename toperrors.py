# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 10:04:24 2018

@author: Tom Wood

toperrors: a package to read through topas input (or output) files and extract
the uncertainties calculated therein
"""

fpath = "C:/Users/vgx18551/Documents/Data/Polaris_Jun18_Faradion_cathode"
fpath += "/Standards/POL109230-NBS-640b-Si-Riet-01.inp"

extract_all = False

#parameter names/values to record
refined_params = []
refp_vals = []
refp_uncs = []
unrefined_params = []
defines = []
#flags for finding comments and comment blocks
ignore = False 
ignoredef = False 
define = False 
ifdef = False 
endif = False

def line_comment(s, ignore):
    """Looks for ' and returns (modified) string and break_bool"""
    break_bool = False
    if ignore:
        res = s
    else:
        if "'" in s:
            res = s[:s.index("'")]
            break_bool = True
        else:
            res = s
    return res, break_bool

def block_comment(s, ignore):
    """Looks for /* or */ and raises flags/modifies strings accordingly"""
    continue_bool = False
    if not ignore:
        if '/*' in s:
            ig_bool = True
            res = s[:s.index('/*')]
        else:
            ig_bool = False
            res = s
    else:
        if '*/' in s:
            ig_bool = False
            res = s[s.index('*/')+2:]
        else:
            ig_bool = True
            res = s
            continue_bool = True
    return res, ig_bool, continue_bool

def is_define(s):
    """Return bool for whether s is a define statement"""
    if s == '#define':
        res = True
    else:
        res = False
    return res

def is_ifdef(s):
    """Return bool for whether s is an ifdef statement"""
    if s == '#ifdef':
        res = True
    else:
        res = False
    return res

def is_endif(s):
    """Return bool for whether s is an endif statement"""
    if s == '#endif':
        res = True
    else:
        res = False
    return res

def set_ignoredef(s, ifdef, defines, ignoredef, endif):
    """Sets flags for whether in a non-defined block or not"""
    if ifdef:
        if s in defines:
            ignoredef = False
        else:
            ignoredef = True
        continue_bool = False
    else:
        if ignoredef:
            if endif:
                ignoredef = False
                continue_bool = False
            else:
                continue_bool = True
        else:
            continue_bool = False
    return ignoredef, continue_bool

# This needs to find the parameter values---comments seem to have been dealt
# with nicely.


with open(fpath, 'r') as f:
    for i, line in enumerate(f):
        string = "line %d: ignoredef = %s" % (i, ignoredef)
        print(string)
        if i > 50:
            break
        for l in line.split():
            s, break_bool = line_comment(l, ignore)
            if not break_bool:
                s, ignore, continue_bool = block_comment(s, ignore)
                if continue_bool:
                    continue
            #sort out ifdefs here
            if define:
                defines.append(s)
            ignoredef, continue_bool = set_ignoredef(s, ifdef, defines, 
                                                     ignoredef, endif)
            ifdef = False #reset ifdef
            #actually reading the string here
            endif = is_endif(s)
            if continue_bool:
                continue
            ifdef = is_ifdef(s)
            define = is_define(s)
            
            #put in parameter gets here
            
            if break_bool:
                break