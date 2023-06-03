from sympy.parsing.latex import parse_latex

from dae_equiv_judge.equation_group import EquationGroup


def latex_to_sympy_obj(latex_eq_list):
    sympy_obj_list = []
    for latex_eq in latex_eq_list:
        assert "=" in latex_eq
        sympy_obj_list.append(parse_latex(latex_eq))
    return sympy_obj_list


def latex_to_eq_group(latex_eq_list):
    sympy_obj_list = latex_to_sympy_obj(latex_eq_list)
    eq_group = EquationGroup(sympy_obj_list)
    return eq_group
