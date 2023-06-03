import os
from collections import defaultdict

import sympy as sy


def _index_of_equation_with_target(targets, eq_list) -> defaultdict:
    """
    Outputs the correspondence between the within-shared variables/terms
    and the equations in the equation groups.

    Args:
        targets: within group shared variables set
        eq_list: equation list
    """
    target2eqid_dict = defaultdict(list)

    for target in targets:
        for idx, eq in enumerate(eq_list):
            if target in eq.free_symbols:
                target2eqid_dict[target].append(idx)
    return target2eqid_dict


def _reduce_the_number_of_equation(eq_group, targets=None):

    if not eq_group.within_group_shared_var_set:
        return eq_group.eq_list

    if not targets:
        return eq_group.eq_list

    eq_list_copy = eq_group.eq_list.copy()

    target2eqid_dict = _index_of_equation_with_target(
        eq_group.within_group_shared_var_set, eq_list_copy
    )

    for target in targets:
        solution_for_target = []

        if target not in target2eqid_dict:
            continue

        for eqid in target2eqid_dict[target]:
            try:
                """
                Obtain solution of each equation for target.
                Obtained solution is stored into eqid2solution_for_target.

                Example:
                input: eq_list = [a=b, a=c, b=c], target=a
                output :eqid2solution_for_target={0:b, 1:c}
                """
                solution = sy.solve(eq_list_copy[eqid], target)
                if len(solution) == 1:
                    simplicity = 0
                    solution_for_target.append(
                        {
                            "eqid": eqid,
                            "solution": solution[0],
                            "simplicity": simplicity,
                        }
                    )
            except BaseException:
                solution_for_target.append(
                    {"eqid": eqid, "solution": None, "simplicity": 1_000_000}
                )
        if not solution_for_target:
            continue

        sorted_solution_for_target = sorted(
            solution_for_target, key=lambda x: x["simplicity"]
        )
        solution_for_substitution = sorted_solution_for_target[0]["solution"]
        eqid_for_substitution = sorted_solution_for_target[0]["eqid"]

        # substitute solution_for_substitution to the other equations
        for eqid in target2eqid_dict[target]:
            if eqid == eqid_for_substitution:
                continue
            eq_old = eq_list_copy[eqid]
            eq_new = eq_old.subs(target, solution_for_substitution)
            eq_list_copy[eqid] = eq_new

        eq_list_copy.pop(eqid_for_substitution)
        targets.remove(target)
        break

    if eq_list_copy == eq_group.eq_list:
        print("Could not reduce the number of equation.")
        return eq_group.eq_list

    # EquationGroup needs to be updated,
    # because its within_shared_variable can be changed.
    new_eq_group = EquationGroup(eq_list_copy)
    return _reduce_the_number_of_equation(new_eq_group, targets=targets)


class EquationGroup:
    def __init__(self, eq_list):
        """Represents an equation group.

        Args:
            eq_list (list[sympy.core.relational.Equality]): list of equations
        """

        self._eq_list = eq_list

        var_set = set()
        for eq in self.eq_list:
            var_set = var_set.union(eq.free_symbols)
        self._var_set = var_set

        within_group_shared_var_set = set()
        for var in self.var_set:
            n_var = 0
            for eq in self.eq_list:
                if var in eq.free_symbols:
                    n_var += 1
                if n_var > 1:
                    within_group_shared_var_set.add(var)
                    continue
        self._within_group_shared_var_set = within_group_shared_var_set

    def __eq__(self, other):
        """
        This funtion enables the operator "==" to judge the equivalence
        between two equation groups, such as eq_group_1 == eq_group_2.
        """
        return self.is_equivalent_eq_groups(self, other)

    @property
    def eq_list(self):
        return self._eq_list

    @property
    def var_set(self):
        return self._var_set

    @property
    def within_group_shared_var_set(self):
        return self._within_group_shared_var_set

    @classmethod
    def is_equivalent_eq_groups(cls, eq_group1, eq_group2):
        """Judges whether eq_group1 and eq_group2 are equivalent.
        The judgment is conducted as follows:
        1. identify variables to be eliminated
        2. eliminate the variables
        3. check one-to-one relationships among equations in both equation groups.
        """

        def get_target_in_two_eq_groups(
            target_cand_eq_group1: set,
            target_cand_eq_group2: set,
        ):
            """
            The variables to be eliminated are obtained.
            The difference set of variables in eq_group1 and eq_group2
            is the variable to be eliminated.

            Args:
                target_cand_eq_group1 (set): variables in eq_group1
                target_cand_eq_group2 (set): variables in eq_group2

            Returns:
                target_set_eq_group1 (set): variables to be eliminated in eq_group1
                target_set_eq_group2 (set): variables to be eliminated in eq_group2

            Example:
                When eq_group1 has variables [a, b, c] and eq_group2 has [a, b, d],
                target_var_eq_group1 = c and target_var_eq_group2 = d.
            """

            target_cand_shared = target_cand_eq_group1 & target_cand_eq_group2
            target_set_eq_group1 = target_cand_eq_group1 - target_cand_shared
            target_set_eq_group2 = target_cand_eq_group2 - target_cand_shared

            return target_set_eq_group1, target_set_eq_group2

        target_var_eq_group1, target_var_eq_group2 = get_target_in_two_eq_groups(
            eq_group1.var_set.copy(),
            eq_group2.var_set.copy(),
        )

        # Check if two equation groups have different variables
        if target_var_eq_group1 or target_var_eq_group2:
            # get eliminatable variables
            if target_var_eq_group1:
                target_var_eq_group1 &= eq_group1.within_group_shared_var_set.copy()
            if target_var_eq_group2:
                target_var_eq_group2 &= eq_group2.within_group_shared_var_set.copy()
            if not (target_var_eq_group1 or target_var_eq_group2):
                print(
                    "Two equation groups has different variables but cannot unify them."
                )
                return False

        if (not target_var_eq_group1) and (not target_var_eq_group2):
            is_same = cls.has_one2one_relationship(eq_group1.eq_list, eq_group2.eq_list)
            return is_same

        else:  # eliminate within shared variables

            if target_var_eq_group1:
                eq_list1_new = _reduce_the_number_of_equation(
                    eq_group=eq_group1, targets=target_var_eq_group1
                )
            else:
                eq_list1_new = eq_group1.eq_list.copy()

            if target_var_eq_group2:
                eq_list2_new = _reduce_the_number_of_equation(
                    eq_group=eq_group2,
                    targets=target_var_eq_group2,
                )
            else:
                eq_list2_new = eq_group2.eq_list.copy()

            eq_group1 = cls(eq_list1_new)
            eq_group2 = cls(eq_list2_new)

            return cls.is_equivalent_eq_groups(eq_group1, eq_group2)

    @classmethod
    def has_one2one_relationship(cls, eq_list1, eq_list2):
        """
        Check one-to-one relationship between two equation groups.
        When all equations have the one-to-one relationship, return True,
        otherwise False.
        """
        equivalent_eq_index_list = []

        for eq2 in eq_list2:
            has_equivalent_eq = False
            for i_eq1, eq1 in enumerate(eq_list1):
                if i_eq1 in equivalent_eq_index_list:
                    continue
                has_equivalent_eq = cls.is_equivalent_eqs(eq1, eq2)

                if has_equivalent_eq:
                    equivalent_eq_index_list.append(i_eq1)
                    break

            if not has_equivalent_eq:
                print("Equation i is not equivalent to any equation in eq_group2.")
                return False
        return True

    @classmethod
    def is_equivalent_eqs(cls, eq1, eq2):
        """Judges whether eq1 and eq2 are equivalent.

        Args:
            eq1 (sympy.core.relational.Equality)
            eq2 (sympy.core.relational.Equality)

        Returns:
            bool: whether two equations are equivalent (True).
        """

        def is_solutions_same(eq1, eq2, symbol):
            solution_eq1 = sy.solve(eq1, symbol)
            solution_eq2 = sy.solve(eq2, symbol)
            if len(solution_eq1) != 1 or len(solution_eq2) != 1:
                return False
            q = sy.simplify(solution_eq1[0] / solution_eq2[0])
            return int(q) == 1

        if eq1.free_symbols != eq2.free_symbols:
            return False

        if eq1 == eq2:
            return True

        for var in eq1.free_symbols:
            try:
                if is_solutions_same(eq1, eq2, var):
                    return True

            except BaseException:
                continue

        return False
