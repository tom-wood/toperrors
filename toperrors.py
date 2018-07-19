# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 10:04:24 2018

@author: Tom Wood

toperrors: a package to read through topas input (or output) files and extract
the uncertainties calculated therein
"""

fpath = "C:/Users/vgx18551/Documents/Data/Polaris_Jun18_Faradion_cathode"
fpath += "/Standards/POL109230-NBS-640b-Si-Riet-01.inp"

extra_values = ['r_wp']
#extract_all = False


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
    if len(s) > 1 and s[1][0].isalpha() == False:
        if not s[1][-1].isdigit():
            s[1] = s[1][:-1]
        u = float(s[1])
    else:
        u = 0.
    return p, u
    

#parameter names/values to record
bkg_count = 0
unnamed_count = 0
refined_params = []
refp_vals = []
refp_uncs = []
unrefined_params = []
unrefp_vals = []
unrefp_uncs = []
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
equal_defer = False
semicolon = False
extract_next = False
#flags for finding macros
macro = False
#keywords
ignore_keys = ['xdd', 'r_wp', 'r_exp', 'gof', 'r_exp_dash', 'r_wp_dash',
               'r_p_dash', 'weighted_Durbin_Watson', 
               'penalties_weighting_K1', 'start_X', 'finish_X', 'fit_obj', 
               'Rp', 'Rs', 'lam', 'la', 'lo', 'lh', 'lg', 'x_calculation_step']
single_keys = ['continue_after_convergence', 'do_errors', 'str',  
               'view_structure', 'Dummy_Peak_Shape',]
extract_keys = ['a', 'b', 'c', 'al', 'be', 'ga', 'prm', 'volume']
#counting the number of times extra_values occur (for multiple r_wps etc.)
count_extra = [0 for s in extra_values]
count_extract = [0 for s in extract_keys]

with open(fpath, 'r') as f:
    for i, line in enumerate(f):
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
            #find macros and ignore
            if macro:
                if l[-1] == '}':
                    macro = False
                continue
            if l == 'macro':
                macro = True
            #work out background parameters
            if bkg:
                if l == '@':
                    refined = True
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
                        unrefp_uncs.append(u)
                        unrefined_params.append(p_name)
                    continue
            refined = False
            bkg = is_bkg(l)
            #work out prm parameters
            if extract_next:
                if l == '@':                  
                    refined = True
                    continue
                else:
                    if l[0] == '!':
                        p_name = l[1:]
                        continue
                    elif l[0].isalpha():
                        if equal_defer:
                            continue
                        else:
                            if semicolon:
                                semicolon = False
                                prm = False
                                continue
                            else:
                                refined = True
                                p_name = l
                            continue
                    elif l[0] == '=':
                        equal_defer = True
                        if l[-1] == ';':
                            equal_defer = False
                            semicolon = True
                        continue
                    elif l[0] == ';':
                        equal_defer = False
                        semicolon = True
                        continue
                    elif l[0] == '-' or l[0].isdigit():
                        if equal_defer:
                            if l[-1] == ';':
                                semicolon = True
                                equal_defer = False
                            continue
                        else:
                            p, u = extract_params(l)
                            if refined:
                                refined_params.append(p_name)
                                refp_vals.append(p)
                                refp_uncs.append(u)
                                refined = False
                            else:
                                unrefined_params.append(p_name)
                                unrefp_vals.append(p)
                                unrefp_uncs.append(u)  
                                print('%s added on line %d' %(p_name, i+1))
                            semicolon = False
                            extract_next = False
                    elif l[0] == ':':
                        if semicolon:
                            continue
                    else:
                        if l[-1] == ';':
                            semicolon = True
                            equal_defer = False
                        continue
            #prm = is_prm(l)
            if l in extra_values:
                print('%s extra value' % l)
                extract_next = True
                p_name = l
                d = extra_values.index(l)
                if count_extra[d] != 0:
                    p_name += str(count_extra[d])
                count_extra[d] += 1
            if l in extract_keys:
                print('%s extract key' % l)
                extract_next = True
                p_name = l + str(count_extract[extract_keys.index(l)])
                count_extract[extract_keys.index(l)] += 1
            
            #This breaks the line when a ' comment out has been used
            if break_bool:
                break