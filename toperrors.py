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


#import re

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

def is_bkg(s):
    """Return boolean depending on whether string indicates bkg"""
    if s == 'bkg':
        return True
    else:
        return False

def is_prm(s):
    """Return boolean depending on whether string indicates prm"""
    if s == 'prm':
        return True
    else:
        return False

def extract_params(s):
    """Return parameter value and uncertainty from string"""
    s = s.split('_')
    if not s[0][-1].isdigit():
        s[0] = s[0][:-1]
    p = float(s[0])
    if len(s) > 1:
        if not s[1][-1].isdigit():
            s[1] = s[1][:-1]
        u = float(s[1])
    else:
        u = 0.
    return p, u
    

#parameter names/values to record
bkg_count = 0
#unnamed_count = 0
refined_params = []
refp_vals = []
refp_uncs = []
unrefined_params = []
unrefp_vals = []
defines = []
#flags for finding comments and comment blocks
ignore = False 
ignoredef = False 
define = False 
ifdef = False 
endif = False
#flags for finding parameters
bkg = False
refined = False

with open(fpath, 'r') as f:
    for i, line in enumerate(f):
        #string = "line %d: ignoredef = %s" % (i, ignoredef)
        #print(string)
        #if i > 50:
        #    break
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
            #check for background parameters
            #check for @ parameters
            #check for prm parameters
            #check for macro parameters
            if bkg:
                if l == '@':
                    refined = True
                    print('found @')
                    continue
                elif l[0].isalpha() == False:
                    p, u = extract_params(l)
                    p_name = 'bkg' + str(bkg_count)
                    bkg_count += 1
                    if refined:
                        refp_vals.append(p)
                        refp_uncs.append(u)
                        refined_params.append(p_name)
                    else:
                        unrefp_vals.append(p)
                        unrefined_params.append(p_name)
                    continue
            refined = False                    
            bkg = is_bkg(l)
            if bkg:
                print('set bkg')
            
            if break_bool:
                break