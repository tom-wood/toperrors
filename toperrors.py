# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 10:04:24 2018

@author: Tom Wood

toperrors: a package to read through topas input (or output) files and extract
the uncertainties calculated therein
"""
##################################################
#USERS SHOULD VARY THE PARAMETERS BELOW
##################################################
fpath = "C:/Users/vgx18551/Documents/Data/Polaris_Nov15_TMnitriding/Mn1_inps/"
fpath += "Batch_inps/"

#fnames just has to be a list of appropriate filepaths (below is a suggested
#method of creating said list)
fnames = [fpath + str(i) + '.inp' for i in range(84652, 84660)]

#out_name is the filepath to save the values to
out_name = fpath + 'test.txt'

extra_values = ['r_wp', 't2', 'mu0', 'mu1']
macro_keys = ['Cubic', 'Tetragonal', 'Hexagonal', 'Rhombohedral',
              'TOF_Strain_L', 'TOF_Strain_G', 'TOF_CS_L', 'TOF_CS_G',
              'Strain_L', 'Strain_G', 'CS_L', 'CS_G',
              'PV', 'Zero_Error', 'ZE', 'Simple_Axial_Model',
              'One_on_X']

#each macro_name has a corresponding macro_structures describing what to expect
#within the '()' of said macro separted by ','. The key is: 0=ignore,
#1=parameter name/@ symbol, 2=parameter value.
macro_structures = [[2], [2, 2], [2, 2], [2, 2],
                    [1, 2, 0], [1, 2, 0], [1, 2, 0], [1, 2, 0],
                    [1, 2], [1, 2], [1, 2], [1, 2],
                    [1, 1, 1, 1, 2, 2, 2, 2], [1, 2], [1, 2], [1, 2],
                    [1, 2]]

#macro rules:
#(1) macro ending brackets must be followed by a space or newline character
#(2) in macro_structures if there are any 1s, then there must be an equal
#number of 2s.
#(3) no equations (this is just too complicated to parse)
#(4) no min or max within macros (if you're desperate just use the prm keyword)

##################################################
#USERS SHOULD NOT VARY ANYTHING BELOW THIS LINE
##################################################
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
    return s == '#define'

def is_ifdef(s):
    """Return bool for whether s is an ifdef statement"""
    return s == '#ifdef'

def is_endif(s):
    """Return bool for whether s is an endif statement"""
    return s == '#endif'

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
    return s == 'bkg'

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
                        unrefp_uncs, macro_name, macro_count, refined=[],
                        need_name=True, ignores=[], wait_for_comma=False):
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
        refined (list): list of booleans as to which parameters are refined
        or not.
        need_name (bool): determines whether next parameter needs a name 
        generated or otherwise
        ignores (list): booleans for whether parameter is elsewhere defined
        wait_for_comma (bool): determines whether to ignore all things before
        the next comma (used to ignore min and max arguments etc.).
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
        refined (list): updated list of refined booleans
        need_name (bool): updated need_name boolean
        ignores (list): updated ignore list
        wait_for_comma (bool): updated wait_for_comma boolean
    """
    #print(s)
    #print(wait_for_comma)
    new_exp_val = False
    end_value = False
    del_first = False
    s_split = s.split(',')
    if wait_for_comma:
        if ',' in s:
            wait_for_comma = False
            del_first = True
        else:
            s_split = []
            #print('yes')
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
        del_first = True
    if del_first:
        del s_split[0]
    #print(s_split)
    for i, ss in enumerate(s_split):
        #print('s_split string: %s' % ss)
        if len(macro_structure) == ms_count:
            break
        if ss and ss[0] == ')':
            break
        if ss == 'min' or ss == 'max':
            wait_for_comma = True
            break
        if macro_structure[ms_count] == 1:
            if ss == '':
                p_name = macro_name + str(macro_count)
                macro_count += 1
                unrefined_params.append(p_name)
                refined.append(False)
                ignores.append(False)
            elif ss[0] == '!':
                p_name = ss[1:]
                if p_name in unrefined_params:
                    ignores.append(True)
                else:
                    unrefined_params.append(p_name)
                    refined.append(False)
                    ignores.append(False)
            elif ss[0] == '@':
                p_name = macro_name + str(macro_count)
                macro_count += 1
                refined_params.append(p_name)
                refined.append(True)
                ignores.append(False)
            else:
                if ss in refined_params:
                    ignores.append(True)
                else:
                    refined_params.append(ss)
                    refined.append(True)
                    ignores.append(False)
        elif macro_structure[ms_count] == 2:
            if gen_names:
                if ss[0] == '!' or ss[0].isalpha():
                    if ss[0] == '!':
                        if ss[1:] in unrefined_params:
                            ignores.append(True)
                        else:
                            unrefined_params.append(ss[1:])
                            refined.append(False)
                            ignores.append(False)
                    else:
                        if ss in refined_params:
                            ignores.append(True)
                        else:
                            refined_params.append(ss)
                            refined.append(True)
                            ignores.append(False)
                    need_name = False
                else:
                    if need_name:
                        p_name = macro_name + str(macro_count)
                        macro_count += 1
                        unrefined_params.append(p_name)
                        refined.append(False)
                    if not ignores or not ignores[0]:
                        p, u = extract_params(ss)
                        if refined[0]:
                            refp_vals.append(p)
                            refp_uncs.append(u)
                        else:
                            unrefp_vals.append(p)
                            unrefp_uncs.append(u)
                        del refined[0]
                        need_name = True
                    if ignores:
                        del ignores[0]
            else:
                if not ignores or not ignores[0]:
                    p, u = extract_params(ss)
                    if refined[0]:
                        refp_vals.append(p)
                        refp_uncs.append(u)
                    else:
                        unrefp_vals.append(p)
                        unrefp_uncs.append(u)
                    del refined[0]
                if ignores:
                    del ignores[0]
        if i < len(s_split)-1:
            ms_count += 1
    if s.count(',') >= len(s_split) and s.count(','):
        ms_count += 1
    output = end_value, ms_count, new_exp_val, macro_count, refined_params, \
           refp_vals, refp_uncs, unrefined_params, unrefp_vals, unrefp_uncs,\
           refined, need_name, ignores, wait_for_comma  
    #print(output)
    return output

def test_macro_func(test_num=0):
    tests = ['prm_name, 24.0_1.3, prm_name2, 32.0)', 
             'prm_name , 24.0_1.3 , prm_name2 , 32.0 )',
             '@ , 24.0_1.3, @, 32.0)',
             ' , 24.0_1.3, , 32.0 )',
             ' , 24.0_1.3, !prm_name, 32.0_14.3)',
             ' 24.0 ,32.0)',
             '!prm_name 24.0, !prm_name2 32.0)',
             '!prm_name 24.0,!prm_name2 32.0)',
             'prm_name,24.0_1.3,prm_name2,32.0)',
             'prm_n, 24.0_1.3, prm_n2, 32.0)',
             'prm_n, 24.0_1.3, t1)',
             'prm_name, 24.0_1.3 min 10 max 30, prm_name2, 32.0 max 40)',]
    strucs = [[1, 2, 1, 2],
              [1, 2, 1, 2],
              [1, 2, 1, 2],
              [1, 2, 1, 2],
              [1, 2, 1, 2],
              [2, 2],
              [2, 2],
              [2, 2],
              [1, 2, 1, 2],
              [1, 2, 1, 2],
              [1, 2, 0],
              [1, 2, 1, 2],]
    inputs = [(0, 0, False, [], True, [], [], [], [], [], [], [], False),
              (0, 0, False, [], True, [], [], [], [], [], [], [], False),
              (0, 0, False, [], True, [], [], [], [], [], [], [], False),
              (0, 0, True, [], True, [], [], [], [], [], [], [], False),
              (0, 0, True, [], True, [], [], [], [], [], [], [], False),
              (0, 0, False, [], True, [], [], [], [], [], [], [], False),
              (0, 0, False, [], True, [], [], [], [], [], [], [], False),
              (0, 0, False, [], True, [], [], [], [], [], [], [], False),
              (0, 0, False, [], True, [], [], [], [], [], [], [], False),
              (0, 0, False, [], True, ['prm_n'], [2.0], [0.0], [], [], [], [],
               False),
              (0, 0, False, [], True, [], [], [], [], [], [], [], False),
              (0, 0, False, [], True, [], [], [], [], [], [], [], False),
              ]
    outputs = [(True, 3, False, 0, ['prm_name', 'prm_name2'], [24.0, 32.0],
                [1.3, 0.], [], [], [], [], True, [], False),
               (True, 3, False, 0, ['prm_name', 'prm_name2'], [24.0, 32.0],
                [1.3, 0.], [], [], [], [], True, [], False),
               (True, 3, False, 2, ['mn0', 'mn1'], [24.0, 32.0],
                [1.3, 0.], [], [], [], [], True, [], False),
               (True, 3, False, 2, [], [], [], ['mn0', 'mn1'], [24.0, 32.0], 
                [1.3, 0.], [], True, [], False),
               (True, 3, False, 1, [], [], [], ['mn0', 'prm_name'],
                [24.0, 32.0], [1.3, 14.3], [], True, [], False),
               (True, 1, False, 2, [], [], [], ['mn0', 'mn1'], [24.0, 32.0],
                [0.0, 0.0], [], True, [], False),
               (True, 1, False, 0, [], [], [], ['prm_name', 'prm_name2'], 
                [24.0, 32.0], [0.0, 0.0], [], True, [], False),
               (True, 1, False, 0, [], [], [], ['prm_name', 'prm_name2'], 
                [24.0, 32.0], [0.0, 0.0], [], True, [], False),
               (True, 3, False, 0, ['prm_name', 'prm_name2'], [24.0, 32.0],
                [1.3, 0.], [], [], [], [], True, [], False),
               (True, 3, False, 0, ['prm_n', 'prm_n2'], [2.0, 32.0],
                [0., 0.], [], [], [], [], True, [], False),
               (True, 2, False, 0, ['prm_n'], [24.0],
                [1.3], [], [], [], [], True, [], False),
               (True, 3, False, 0, ['prm_name', 'prm_name2'], [24.0, 32.0],
                [1.3, 0.], [], [], [], [], True, [], True),
              ]
    test = tests[test_num].split()
    ms_count, macro_count, exp_val, refined, nn, rpn, rpv, rpu, upn, upv, upu,\
    ignores, wfc = inputs[test_num]
    struc = strucs[test_num]
    for t in test:
#        print(t)
#        print('%s, %s, %s, %s, %s' % (ms_count, exp_val, macro_count,
#                                          refined, nn))
        ev, ms_count, exp_val, macro_count, rpn, rpv, rpu, upn, upv, upu,\
        refined, nn, ignores, wfc =\
        extract_macro_value(t, ms_count, struc, exp_val, rpn, rpv, rpu, upn, 
                            upv, upu, 'mn', macro_count, refined, nn, ignores,
                            wfc)
#        print('%s, %s, %s, %s, %s, %s %s' % (ev, ms_count, exp_val, macro_count,
#                                             refined, nn, ignores))
#        print(upn)
#        print(upv)
    #check against outputs
    output = outputs[test_num]
    new_output = [ev, ms_count, exp_val, macro_count, rpn, rpv, rpu,
                  upn, upv, upu, refined, nn, ignores, wfc]
    bools = []
    for i, o in enumerate(output):
        bools.append(new_output[i] == o)
    if all(bools):
        print("Expected output")
    else:
        print("Unexpected output")
    return bools, new_output, test
    
        
def get_values(fpath, extra_values, macro_keys, macro_structures,
               ignore_bkg=True):
    """Extract all parameter values and uncertainties
    
    Args:
        fpath (str): filepath of file to read for values
        extra_values (list): list of extra values unlikely to be picked up as
        refined or unrefined parameters (e.g. gof and r_wp).
        macro_keys (list): list of macro keywords
        macro_structures (list): list of macro structures for each macro
        keyword.
        ignore_bkg (bool): determines whether to extract bkg parameters or not
    """
    #parameter names/values to record
    bkg_count = 0
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
    macro_k = False
    #keywords
    extract_keys = ['prm']
    struc_keys = ['a', 'b', 'c', 'al', 'be', 'ga', 'volume', 'scale']
    site_keys = ['x', 'y', 'z', 'beq']
    #macro keys are at the top of the file (so users will know the structure for
    #putting in their own macros).
    macro_counts = [0 for s in macro_keys]
    #counting the number of times extra_values occur (for multiple r_wps etc.)
    count_extra = [0 for s in extra_values]
    count_extract = [0 for s in extract_keys]
    #count number of phases
    phase_count = 0
    
    with open(fpath, 'r') as f:
        for i, line in enumerate(f):
            #print(i)
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
                if not ignore_bkg:
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
                                    extract_next = False
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
                                if p_name not in refined_params and p_name \
                                not in unrefined_params:
                                    if refined:
                                        refined_params.append(p_name)
                                        refp_vals.append(p)
                                        refp_uncs.append(u)
#                                        print('R %s added on line %d' %(p_name, 
#                                                                        i+1))
                                    else:
                                        unrefined_params.append(p_name)
                                        unrefp_vals.append(p)
                                        unrefp_uncs.append(u)
#                                        print('U %s added on line %d' %(p_name, 
#                                                                        i+1))
                                semicolon = False
                                extract_next = False
                                refined = False
                        elif l[0] == ':':
                            if semicolon:
                                continue
                        else:
                            if l[-1] == ';':
                                semicolon = True
                                equal_defer = False
                            continue
                if l in extra_values:
                    #print('%s extra value' % l)
                    extract_next = True
                    p_name = l
                    d = extra_values.index(l)
                    if count_extra[d] != 0:
                        p_name += '_' + str(count_extra[d])
                    count_extra[d] += 1
                if l in extract_keys:
                    #print('%s extract key' % l)
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
                        #print('%s struc key' % l)
                        extract_next = True
                if site_name:
                    current_site = l
                    site_name = False
                if site:
                    if l in site_keys:
                        p_name = '_'.join([ph_name, current_site, l])
                        #print('%s site key' % l)
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
                if macro_k:
                    ev, ms_count, exp_val, macro_count, refined_params, refp_vals,\
                    refp_uncs, unrefined_params, unrefp_vals, unrefp_uncs,\
                    refined_bools, nn, ignores, wfc = \
                    extract_macro_value(l, ms_count, struc, exp_val, 
                                        refined_params, refp_vals, refp_uncs,
                                        unrefined_params, unrefp_vals,
                                        unrefp_uncs, macro_name, macro_count, 
                                        refined_bools, nn, ignores, wfc)
                    if ev:
                        macro_counts[macro_i] = macro_count
                        macro_k = False
                if l.split('(')[0] in macro_keys:
                    macro_k = True
                    macro_i = macro_keys.index(l.split('(')[0])
                    ms_count = 0
                    struc = macro_structures[macro_i]
                    macro_name = macro_keys[macro_i]
                    macro_count = macro_counts[macro_i]
                    refined_bools = []
                    nn = True
                    ignores = []
                    wfc = False
                    ms = l.split('(')[1]
                    if ms == ',' or ms == '':
                        exp_val = True
                    else:
                        exp_val = False
                    if ms:
                        ev, ms_count, exp_val, macro_count, refined_params,\
                        refp_vals, refp_uncs, unrefined_params, unrefp_vals,\
                        unrefp_uncs, refined_bools, nn, ignores, wfc =\
                        extract_macro_value(ms, ms_count, struc, exp_val,
                                            refined_params, refp_vals,
                                            refp_uncs, unrefined_params, 
                                            unrefp_vals, unrefp_uncs, 
                                            macro_name, macro_count, 
                                            refined_bools, nn, ignores, wfc)
                        if ev:
                            macro_counts[macro_i] = macro_count
                            macro_k = False
                #This breaks the line when a ' comment out has been used
                if break_bool:
                    break
    output = (refined_params, refp_vals, refp_uncs, unrefined_params,
              unrefp_vals, unrefp_uncs)
    return output

def find_extra_values(extra_values, params):
    """Return indices and values of extra_values found in params"""
    evis, evals = [], []
    for ev in extra_values:
        for i, p in enumerate(params):
            if len(p) >= len(ev) and p[:len(ev)] == ev:
                p_bs = [True if s.isdigit() or s == '_' else False for s in
                        p[len(ev):]]                        
                if all(p_bs):
                    evis.append(i)
                    evals.append(p)
    return evis, evals
                
def get_multiple_values(out_name, fnames, extra_values, macro_keys,
                        macro_structures, save_all=False, append=False,
                        print_warnings=True, interleave=True, ignore_bkg=True):
    """Save multiple parameter values and uncertainties into a file
    
    Args:
        out_name (str): filepath where values will be written
        fnames (list): list of filenames to read
        extra_values (list): list of extra values to record (tend to be values
        rather than parameters).
        macro_keys (list): list of macro keywords
        macro_structures (list): list of macro structures
        save_all (bool): whether to save all parameters or just the refined
        parameters along with the extra values.
        append (bool): whether to append values out file or overwrite
        print_warnings (bool): whether to print_warnings or not
        interleave (bool): interleaves uncertainties with parameter values
        (this is default behaviour); if False then puts uncertainties in
        second half of set of columns.
        ignore_bkg (bool): determines whether to extract bkg parameters or not
    Returns:
        missing_files (list): list of indices to missing filenames in fnames
    """
    out_strs = ['refined parameters', 'urefined parameters']
    success_open = False
    missing_files = []
    for ifn, fn in enumerate(fnames):
        try:
            output = get_values(fn, extra_values, macro_keys, 
                                macro_structures, ignore_bkg)
        except IOError:
            if print_warnings:
                print('File %s missing---moved onto next file' % fn)
            missing_files.append(ifn)
            continue
        if not success_open:
            success_open = True
            out0 = output
            fn0 = fn
            if not append:
                if save_all:
                    save_names = output[0] + output[3]
                else:
                    evis, evals = find_extra_values(extra_values,
                                                    output[3])
                    save_names = output[0] + evals
                unc_names = [sn + '_unc' for sn in save_names]
                if interleave:
                    save_names = [v for p in zip(save_names, unc_names) for v
                                  in p]
                else:
                    save_names += unc_names
                save_names = ' '.join(save_names) + '\n'
                with open(out_name, 'w') as f:
                    f.write(save_names)
        else:
            if print_warnings:
                for i0 in [0, 3]:
                    for i1, obit in enumerate(output[i0]):
                        if out0[i0][i1] != obit:
                            print("In %s, %s has %s at position %d, whereas\
                                  %s has %s" % (out_strs[i0], fn, obit, i1, 
                                                fn0, out0[i0][i1]))
                            continue
        if save_all:
            save_vals = output[1] + output[4]
            save_uncs = output[2] + output[5]
        else:
            evis = find_extra_values(extra_values, output[3])[0]
            save_vals = output[1] + [output[4][evi] for evi in evis]
            save_uncs = output[2] + [output[5][evi] for evi in evis]
        if interleave:
            save_vals = [v for p in zip(save_vals, save_uncs) for v in p]
        else:
            save_vals += save_uncs
        save_vals = [str(sv) for sv in save_vals]
        save_vals = ' '.join(save_vals) + '\n'
        with open(out_name, 'a') as f:
            f.write(save_vals)
    return missing_files