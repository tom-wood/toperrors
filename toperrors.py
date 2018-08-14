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

macro_keys = ['Cubic', 'Tetragonal', 'Hexagonal', 'Rhombohedral',
              'TOF_Strain_L', 'TOF_Strain_G', 'TOF_CS_L', 'TOF_CS_G',
              'Strain_L', 'Strain_G', 'CS_L', 'CS_G']

#each macro_name has a corresponding macro_structures describing what to expect
#within the '()' of said macro separted by ','. The key is: 0=ignore,
#1=parameter name/@ symbol, 2=parameter value.
macro_structures = [[2], [2, 2], [2, 2], [2, 2],
                    [1, 2, 0], [1, 2, 0], [1, 2, 0], [1, 2, 0],
                    [1, 2], [1, 2], [1, 2], [1, 2]]

#macro rules:
#(1) macro ending brackets must be followed by a space or newline character
#(2) in macro_structures if there are any 1s, then there must be an equal
#number of 2s.
#(3) no equations with other parameter names in parameter value fields (this is
#just too complicated to parse)

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

def extract_macro_value(s, ms_count, macro_structure, exp_val, refined_params,
                        refp_vals, refp_uncs, unrefined_params, unrefp_vals,
                        unrefp_uncs, macro_name, macro_count, refined=False,
                        need_name=False):
    """Return parameter value and uncertainty from string
    
    Args:
        s (str): string to extract macro value from
        ms_count (int): counter denoting how far into macro_structure to begin
        macro_structure (list): list of value types to expect
        exp_val (bool): determines whether next value is expected before comma
        or has already been recorded (deals with values that are just spaces,
        i.e. unrefined values with no name).
        refined_params (list): list of strings of refined parameter names
        refp_vals (list): list of refined parameter values
        refp_uncs (list): list of refined parameter uncertainties
        unrefined_params (list): list of strings of unrefined parameter names
        unrefp_vals (list): list of unrefined parameter values
        unrefp_uncs (list): list of unrefined parameter uncertainties
        macro_name (str): name of macro (for unnamed parameters)
        macro_count (int): counter for unnamed parameters
        refined (bool): determines whether next parameter is refined or not
        need_name (bool): determines whether next parameter needs a name 
        generated or otherwise
    Returns:
        end_value (bool): if True, end of macro has been found
        ms_count (int): updated ms_count counter
        new_exp_val: updated exp_val boolean
        macro_count (int): updated macro_count counter
        refined_params (list): updated refined parameters
        refp_vals (list): updated refined values
        refp_uncs (list): updated refined uncertainties
        unrefined_params (list): updated unrefined parameters
        unrefp_vals (list): updated unrefined values
        unrefp_uncs (list): updated unrefined uncertainties
        refined (bool): updated refined boolean
        need_name (bool): updated need_name boolean
    """
    new_exp_val = False
    end_value = False
    s_split = s.split(',')
    if 1 in macro_structure:
        gen_names = False
    else:
        gen_names = True
    if s[-1] == ',':
        del s_split[-1]
        new_exp_val = True
    elif s[-1] == ')':
        end_value = True
    if not exp_val and s[0] == ',':
        del s_split[0]
    for ss in s_split:
#        print('s_split string: %s' % ss)
        if len(macro_structure) == ms_count:
            break
        if macro_structure[ms_count] == 1:
            if ss == '':
                p_name = macro_name + str(macro_count)
                macro_count += 1
                unrefined_params.append(p_name)
                refined = False
            elif ss[0] == '!':
                p_name = ss[1:]
                unrefined_params.append(p_name)
                refined = False
            elif ss[0] == '@':
                p_name = macro_name + str(macro_count)
                macro_count += 1
                refined_params.append(p_name)
                refined = True
            else:
                refined_params.append(ss)
                refined = True
        elif macro_structure[ms_count] == 2:
            if gen_names:
                if ss[0] == '!' or ss[0].isalpha():
                    if ss[0] == '!':
                        unrefined_params.append(ss[1:])
                        refined = False
                    else:
                        refined_params.append(ss)
                        refined = True
                    need_name = False
                else:
                    if need_name:
                        p_name = macro_name + str(macro_count)
                        macro_count += 1
                        unrefined_params.append(p_name)
                        refined = False
                    p, u = extract_params(ss)
                    if refined:
                        refp_vals.append(p)
                        refp_uncs.append(u)
                    else:
                        unrefp_vals.append(p)
                        unrefp_uncs.append(u)
                    need_name = True
            else:
                p, u = extract_params(ss)
                if refined:
                    refp_vals.append(p)
                    refp_uncs.append(u)
                else:
                    unrefp_vals.append(p)
                    unrefp_uncs.append(u)
                refined = False
        ms_count += 1
    return end_value, ms_count, new_exp_val, macro_count, refined_params, \
           refp_vals, refp_uncs, unrefined_params, unrefp_vals, unrefp_uncs,\
           refined, need_name

def test_macro_func(test_num=0):
    tests = ['prm_name, 24.0_1.3, prm_name2, 32.0)', 
             'prm_name , 24.0_1.3 , prm_name2 , 32.0 )',
             '@ , 24.0_1.3, @, 32.0)',
             ' , 24.0_1.3, , 32.0 )',
             ' , 24.0_1.3, !prm_name, 32.0_14.3)']
    strucs = [[1, 2, 1, 2],
              [1, 2, 1, 2],
              [1, 2, 1, 2],
              [1, 2, 1, 2],
              [1, 2, 1, 2],
              [1, 2, 1, 2]]
    inputs = [(0, 0, False, False, False, [], [], [], [], [], []),
              (0, 0, False, False, False, [], [], [], [], [], []),
              (0, 0, False, False, False, [], [], [], [], [], []),
              (0, 0, True, False, False, [], [], [], [], [], []),
              (0, 0, True, False, False, [], [], [], [], [], [])]
    outputs = [(True, 4, False, 0, ['prm_name', 'prm_name2'], [24.0, 32.0],
                [1.3, 0.], [], [], [], False, False),
               (True, 4, False, 0, ['prm_name', 'prm_name2'], [24.0, 32.0],
                [1.3, 0.], [], [], [], False, False),
               (True, 4, False, 2, ['mn0', 'mn1'], [24.0, 32.0],
                [1.3, 0.], [], [], [], False, False),
               (True, 4, False, 2, [], [],
                [], ['mn0', 'mn1'], [24.0, 32.0], [1.3, 0.], False, False),
               (True, 4, False, 1, [], [], [], ['mn0', 'prm_name'],
                [24.0, 32.0], [1.3, 14.3], False, False),
              ]
    test = tests[test_num].split()
    ms_count, macro_count, exp_val, refined, nn, rpn, rpv, rpu, upn, upv, upu\
    = inputs[test_num]
    struc = strucs[test_num]
    for t in test:
#        print(t)
#        print('%s, %s, %s, %s, %s' % (ms_count, exp_val, macro_count,
#                                          refined, nn))
        ev, ms_count, exp_val, macro_count, rpn, rpv, rpu, upn, upv, upu,\
        refined, nn = extract_macro_value(t, ms_count, struc, exp_val, rpn, 
                                          rpv, rpu, upn, upv, upu, 'mn', 
                                          macro_count, refined, nn)
#        print('%s, %s, %s, %s, %s, %s' % (ev, ms_count, exp_val, macro_count,
#                                          refined, nn))
#        print(upn)
    #check against outputs
    output = outputs[test_num]
    new_output = [ev, ms_count, exp_val, macro_count, rpn, rpv, rpu,
                  upn, upv, upu, refined, nn]
    bools = []
    for i, o in enumerate(output):
        bools.append(new_output[i] == o)
    if all(bools):
        print("Expected output")
    else:
        print("Unexpected output")
    return bools, new_output, test
    
        
"""
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
occ = False
site = False
site_name = False
struc = False
phase_name = False
#flags for finding macros
macro = False
#keywords
ignore_keys = ['xdd', 'r_wp', 'r_exp', 'gof', 'r_exp_dash', 'r_wp_dash',
               'r_p_dash', 'weighted_Durbin_Watson', 
               'penalties_weighting_K1', 'start_X', 'finish_X', 'fit_obj', 
               'Rp', 'Rs', 'lam', 'la', 'lo', 'lh', 'lg', 'x_calculation_step']
single_keys = ['continue_after_convergence', 'do_errors', 'str',  
               'view_structure', 'Dummy_Peak_Shape',]
extract_keys = ['prm']
struc_keys = ['a', 'b', 'c', 'al', 'be', 'ga', 'volume', 'scale']
site_keys = ['x', 'y', 'z', 'beq']
#macro keys are at the top of the file (so users will know the structure for
#putting in their own macros).
macro_counts = [0 for s in macro_keys]
macro_prms = []
#counting the number of times extra_values occur (for multiple r_wps etc.)
count_extra = [0 for s in extra_values]
count_extract = [0 for s in extract_keys]
#count number of phases
phase_count = 0

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
            #find macro definitions and ignore
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
            #deal with structures, sites and occupancies
            if l == 'str':
                site = False
                ph_name = 'phase' + str(phase_count)
                phase_count += 1
                struc = True
            if phase_name:
                if l[-1] == ')':
                    ph_name = l[:-1]
                else:
                    ph_name = l
                if ph_name[0] and ph_name[-1] == '"':
                    ph_name = ph_name[1:-1]
                phase_name = False
            if l[:4] == 'STR(':
                struc = True
                if ',' in l and len(l.split(',')[1]) > 1:
                    if l.split(',')[1][-1] == ')':
                        ph_name = l.split(',')[1][-1][:-1]
                    else:
                        ph_name = l.split(',')[1][-1]
                else:
                    phase_name = True
            if struc:
                if l == 'phase_name':
                    phase_name = True
                elif l in struc_keys:
                    p_name = '_'.join([ph_name, l])
                    print('%s struc key' % l)
                    extract_next = True
            if site_name:
                current_site = l
                site_name = False
            if site:
                if l in site_keys:
                    p_name = '_'.join([ph_name, current_site, l])
                    print('%s site key' % l)
                    extract_next = True
            if l == 'site':
                site = True
                site_name = True
            if occ:
                extract_next = True
                occ = False
                p_name = '_'.join([ph_name, current_site]) + '_occ'
            if l == 'occ':
                occ = True
            #recognize macros
            
            #This breaks the line when a ' comment out has been used
            if break_bool:
                break
            """
##############STILL to do
#(1) Cope with [1, 1, 1, 2, 2, 2] type macro_structures
#(2) Integrate extract_macro_value with main with statement
#(3) Put with statement into a function
#(4) Make good for multiple files