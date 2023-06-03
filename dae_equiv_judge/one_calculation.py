import os

from graphviz import Digraph
import sympy as sy
import copy


class SLTParser:

    var_dic = {}
    func_dic = {}

    def __init__(self, tree_list):

        self._SLT = tree_list
        self.SLT_figure = None
        try:
            self._info = self.get_calculation_info()
            self._get_var_info()
            self.sympy_object_converter = SympyObjectConverter(var_dic=self.var_dic, calculation_info=self._info)
            self._get_SLT_figure()
        except:
            print('fail to retrieve information of variables and calculations')
            self._get_SLT_figure()

    def _get_SLT_figure(self):

        # initialize the SLT figure
        tree_fig = Digraph(format='pdf')
        tree_fig.attr("node", shape="square", style="filled")
        tree_fig.attr("graph", rankdir="LR")
        try:
            self.SLT_figure = self._graph_for_slt(self._SLT, tree_fig)
        except:
            print('fail to get the SLT figure')

    def _get_var_info(self):

        var_list = self.__get_var_info_from_cal_info(cal_info=self._info)

        #ネイピア数やΠなども変数として抽出されるが、
        # ここではSymPyのネイピア数、Πのオブジェクトで置き換える。
        # その他の変数はSymPyのsymbolsメソッドで変数オブジェクトへ変換する

        for var in set(var_list):
            if var not in self.var_dic:
                if var == 'e':
                    self.var_dic[var] = sy.E
                elif var == 'pi':
                    self.var_dic[var] = sy.pi
                else:
                    self.var_dic[var] = sy.symbols(var)

        #ある変数fが他の変数の関数を表す際に、その変数を関数として定義し直す
        for func in self.func_dic:
            diff_vars = [self.var_dic[var]  for var in self.func_dic[func]]
            self.var_dic[func] = sy.Function(func)(*diff_vars)

    def save_SLT_figure(self, path_dir, file_name, if_view=True):
        if os.path.exists(path_dir):
            self.SLT_figure.render(directory=path_dir, filename=file_name, view=if_view, cleanup=True)
        else:
            os.makedirs(path_dir)
            self.SLT_figure.render(directory=path_dir, filename=file_name, view=if_view, cleanup=True)
        return

    @classmethod
    def __get_var_info_from_cal_info(cls, cal_info, var_lst=None):

        if not var_lst:
            var_lst = []

        for elem in cal_info:
            if type(elem) is str:
                if elem not in ['+', '-', '*', '/', '=', '∂'] and not elem.startswith('N!'):
                    var_lst.append(elem)
            else:
                var_lst_nested = cls.__get_var_info_from_cal_info(elem[0])
                if elem[1]:
                    var_lst_nested = cls.__get_var_info_from_cal_info(elem[1], var_lst=var_lst_nested)

                var_lst.extend(var_lst_nested)

        return var_lst

    def get_calculation_info(self):

        formula_element = []

        # A list holding the hierarchical information of a formula
        # is created from SLT-tangents.
        calculation_info_with_func = self.parse_tree(self._SLT, formula_element)

        #logを除いた関数に対する処理、log関数を除くのはlog関数の木構造が特殊だからです
        for var in calculation_info_with_func:

            # ['sin', [STL of 'a', None, 'within']]
            # --> ['sin', [STL of 'a', None, 'sin']]
            if var in ['sin', 'cos', 'tan', 'sec', 'cosec', 'cotan', 'asin', 'acos', 'atan']:
                idx = calculation_info_with_func.index(var)
                if type(calculation_info_with_func[idx+1]) == list:
                    calculation_info_with_func[idx+1][2] = var
                else:   #これは起きえないはず, 関数が作用する数式は<mfence>タグで囲めば、その数式がリストの中に入る。
                    raise Exception('関数が作用する範囲が明確ではありません')

            #expの場合、状況が少し違う
            elif var == 'exp':
                idx = calculation_info_with_func.index(var)
                if type(calculation_info_with_func[idx+1]) == list:
                    calculation_info_with_func[idx+1][2] = var
                    calculation_info_with_func[idx+1][1] = calculation_info_with_func[idx+1][0]
                    calculation_info_with_func[idx+1][0] = ['e']
                else:  # これは起きえないはず, 関数が作用する数式は<mfence>タグで囲めば、その数式がリストの中に入る。
                    raise Exception('関数が作用する範囲が明確ではありません')

            elif type(var) is list and var[-1] == 'log':
                idx = calculation_info_with_func.index(var)
                if type(calculation_info_with_func[idx+1]) is list:
                    logarithm = calculation_info_with_func[idx+1]
                    var[1] = logarithm[0]
                else:
                    raise Exception('関数が作用する範囲が明確ではありません')
                calculation_info_with_func.pop(idx+1)

            #総和の処理がこちらになる
            elif type(var) is list and var[-1] == 'sum':
                idx = calculation_info_with_func.index(var)
                if type(calculation_info_with_func[idx+1]) is list:
                    formula_in_sum = calculation_info_with_func[idx+1]
                    var[3] = [formula_in_sum]
                else:
                    raise Exception('関数が作用する範囲が明確ではありません')

                #varの中の情報を整理する。[加算の対象となる変数, 下限、上限、式、'sum']という具合に
                lower_limit = var[1]
                if len(lower_limit) == 3:
                    var[0] = [lower_limit.pop(0)]
                    lower_limit.pop(0)

                calculation_info_with_func.pop(idx+1)
                # self.var_dic.pop('Σ')

        calculation_info_with_func_copy = copy.deepcopy(calculation_info_with_func)

        for var in calculation_info_with_func:
            # ['sin', [STL of 'a', None, 'sin']]
            # --> [[STL of 'a', None, 'sin']]
            if var in ['sin', 'cos', 'tan', 'sec', 'cosec', 'cotan', 'asin', 'acos', 'atan', 'exp']:
                calculation_info_with_func_copy.remove(var)

        ##20210710 微分の部分を認識し，'frac'を'diff'に変更する，且つ変数の情報も変更する．
        for var in calculation_info_with_func_copy:
            if type(var) is list:
                if var[2] == 'frac':
                    calculation_info_above = var[0]
                    calculation_info_below = var[1]
                    if (calculation_info_above[0]==calculation_info_below[0]) and\
                       (calculation_info_above[0]in ['d', '∂']):
                        #置き換える
                        var[2] = 'diff'
                        calculation_info_above.pop(0)
                        calculation_info_below.pop(0)
                        #変数再定義する
                        diff_func_info = calculation_info_above
                        diff_var_name = calculation_info_below[0]
                        self.__add_func(diff_func_info, diff_var_name)
                        #var_dicからdを削除する いらないかも
                        self.var_dic.pop('d', None)
                        self.var_dic.pop('∂', None)

        return calculation_info_with_func_copy

    def __add_func(self, diff_func_info, diff_var_name):

        var_lst = list(filter(lambda x: isinstance(x, str), diff_func_info))
        for var in var_lst:
            if (var not in ['+', '-', '*', r'/']) and (var != diff_var_name) and (not var.startswith('N!')):
                if var not in self.func_dic:
                    self.func_dic[var] = []
                    self.func_dic[var].append(diff_var_name)
                else:
                    if diff_var_name not in self.func_dic[var]:
                        self.func_dic[var].append(diff_var_name)

        lst_lst = list(filter(lambda x: isinstance(x, list), diff_func_info))

        for lst in lst_lst:
            if lst[0]:
                self.__add_func(lst[0], diff_var_name)
            if lst[1]:
                self.__add_func(lst[1], diff_var_name)

    def to_sympy_object(self):
        return self.sympy_object_converter.get_sympy_object()

    @property
    def slt(self):
        return self._SLT

    @property
    def info(self):
        return self._info

    @classmethod
    def _graph_for_slt(cls, tree_list, tree_fig):

        slt_tree_list = []

        if not tree_list:
           return tree_fig

        else:
            for slt_tree in tree_list:
                if not slt_tree[1].active_children():
                    tree_fig.node(slt_tree[1].tag)
                else:
                    for children_tuple in slt_tree[1].active_children():
                        absolute_path = slt_tree[0]
                        tag_ancestor = slt_tree[1].tag
                        tag_children = children_tuple[1].tag
                        tag_ancestor += ',' + absolute_path
                        absolute_path += children_tuple[0]
                        tag_children += ',' + absolute_path
                        tree_fig.edge(tag_ancestor, tag_children)

                for children_tuple in slt_tree[1].active_children():
                    absolute_path = slt_tree[0]
                    children = children_tuple[1]
                    if children.active_children():
                        absolute_path += children_tuple[0]
                        slt_tree_list.append((absolute_path, children))

            return cls._graph_for_slt(tree_list=slt_tree_list, tree_fig=tree_fig)

    @classmethod
    def deal_with_vtag(cls, tree_list):
        variable = None
        formula = None
        for slt_tree in tree_list:
            variable = slt_tree[1].tag
            children_list = slt_tree[1].active_children()

            if variable.startswith('V!'):
                variable = variable.split('!')[1]
                #三角関数の逆関数をここで捕まえる
                if variable in ['sin', 'cos', 'tan']:
                    for children_tuple in children_list:
                        position = children_tuple[0]
                        if position == 'a' and children_tuple[1].tag == 'N!-1':
                            variable = 'a'+variable

            elif variable.startswith('N!'):
                pass

            for children_tuple in children_list:
                position = children_tuple[0]

                if position == 'b':
                    slt_below = [('', children_tuple[1])]
                    var_info_below = cls(tree_list=slt_below).get_calculation_info()
                    lst = []
                    # ensure N!2 converted to 2 => r_2 instead of r_N!2
                    for idx, elem in enumerate(var_info_below):
                        if elem.startswith('N!'):
                            lst.append(elem.split('!')[1])
                        else:
                            lst.append(elem)
                    var_below = ''.join(lst)
                    variable += '_'+ var_below

                elif position == 'o':
                    # どう処理するか後で考えましょう　これはハット付きの変数　
                    pass

                elif position == 'n':
                    formula = [('', children_tuple[1])]

        return variable, formula

    @classmethod
    def deal_with_fraction(cls, tree_list):

        formula_info_over = None
        formula_info_under = None
        slt_next = None

        for slt_tree in tree_list:
            for children_tuple in slt_tree[1].active_children():
                position = children_tuple[0]
                # 上付き文字に対応する
                if position == 'o':
                    slt_over = [('', children_tuple[1])]
                    formula_info_over = cls(tree_list=slt_over).get_calculation_info()

                elif position == 'u':
                    slt_under = [('', children_tuple[1])]
                    formula_info_under = cls(tree_list=slt_under).get_calculation_info()

                elif position == 'n':
                    slt_next = [('', children_tuple[1])]

        return formula_info_over, formula_info_under, slt_next

    @classmethod
    def deal_with_paren(cls, tree_list):

        formula_info_inside = None
        slt_next = None

        for slt_tree in tree_list:
            for children_tuple in slt_tree[1].active_children():
                position = children_tuple[0]
                if position == 'w':
                    slt_inside = [('', children_tuple[1])]
                    formula_info_inside = cls(tree_list=slt_inside).get_calculation_info()

                elif position == 'n':
                    slt_next = [('', children_tuple[1])]

        return formula_info_inside, slt_next

    @classmethod
    def deal_with_exp(cls, tree_list):
        formula_info_above = None
        for slt_tree in tree_list:
            for children_tuple in slt_tree[1].active_children():
                position = children_tuple[0]
                if position == 'a':
                    slt_above = [('', children_tuple[1])]
                    formula_info_above = cls(tree_list=slt_above).get_calculation_info()
        return formula_info_above

    @classmethod
    def deal_with_root(cls, tree_list):
        formula_info_inside = None
        formula_info_pre_above = None
        slt_next = None
        for slt_tree in tree_list:
            for children_tuple in slt_tree[1].active_children():
                position = children_tuple[0]
                if position == 'w':
                    slt_inside = [('', children_tuple[1])]
                    formula_info_inside = cls(tree_list=slt_inside).get_calculation_info()

                elif position == 'n':
                    slt_next = [('', children_tuple[1])]

                elif position == 'c':
                    slt_pre_above = [('', children_tuple[1])]
                    formula_info_pre_above = cls(tree_list=slt_pre_above).get_calculation_info()

        return formula_info_inside, formula_info_pre_above, slt_next

    @classmethod
    def deal_with_log(cls, tree_list):
        formula_info_below = None
        slt_next = None
        for slt_tree in tree_list:
            for children_tuple in slt_tree[1].active_children():
                position = children_tuple[0]
                if position == 'b':
                    slt_below = [children_tuple]
                    formula_info_below = cls(tree_list=slt_below).get_calculation_info()
                elif position == 'n':
                    slt_next = [children_tuple]
        return formula_info_below, slt_next

    @classmethod
    def deal_with_sigma(cls, tree_list):
        formula_info_under = None
        formula_info_over = None
        slt_next = None
        for slt_tree in tree_list:
            for children_tuple in slt_tree[1].active_children():
                position = children_tuple[0]
                if position == 'u':
                    slt_under = [('', children_tuple[1])]
                    formula_info_under = cls(tree_list=slt_under).get_calculation_info()

                elif position == 'o':
                    slt_over = [('', children_tuple[1])]
                    formula_info_over = cls(tree_list=slt_over).get_calculation_info()

                elif position == 'n':
                    slt_next = [('', children_tuple[1])]

        return formula_info_under, formula_info_over, slt_next

    @classmethod
    def parse_tree(cls, tree_list, formula_element):
        if not tree_list:
            return formula_element

        else:
            for slt_tree in tree_list:
                if slt_tree[1].tag.startswith('O!divide'):
                    numerator, denominator, formula_next = cls.deal_with_fraction([slt_tree])
                    formula_element.append([numerator, denominator, 'frac'])
                    return cls.parse_tree(formula_next, formula_element)

                elif slt_tree[1].tag.startswith('V!') and (not slt_tree[1].tag.startswith('V!log')) \
                        and (not slt_tree[1].tag.startswith('V!∑'))\
                        or slt_tree[1].tag.startswith('N!'):
                    var, formula_next = cls.deal_with_vtag(tree_list)
                    formula_above = cls.deal_with_exp([slt_tree])
                    if formula_above is not None and var not in ['asin', 'acos', 'atan']:
                        formula_element.append([[var], formula_above, 'exp'])
                    else:
                        formula_element.append(var)
                    return cls.parse_tree(formula_next, formula_element)

                elif slt_tree[1].tag.startswith('M!'):
                    formula_within, formula_next = cls.deal_with_paren([slt_tree])
                    formula_above = cls.deal_with_exp([slt_tree])
                    if formula_above is not None:
                        formula_element.append([formula_within, formula_above, 'exp'])
                    else:
                        formula_element.append([formula_within, None, 'within'])
                    return cls.parse_tree(formula_next, formula_element)

                elif slt_tree[1].tag.startswith('V!log'):
                    formula_below, formula_next = cls.deal_with_log([slt_tree])
                    formula_element.append([formula_below, None, 'log'])
                    return cls.parse_tree(formula_next, formula_element)

                elif slt_tree[1].tag.startswith('V!∑'):
                    formula_under, formula_over, formula_next = cls.deal_with_sigma([slt_tree])
                    formula_element.append([None, formula_under, formula_over, None, 'sum'])
                    return cls.parse_tree(formula_next, formula_element)

                elif slt_tree[1].tag.startswith('O!root'):
                    formula_within, formula_pre_above, formula_next = cls.deal_with_root([slt_tree])
                    formula_element.append([formula_within, formula_pre_above, 'root'])
                    return cls.parse_tree(formula_next, formula_element)

                elif slt_tree[1].tag in ['+', '-', '=', '*', r'/', '∂']:
                    formula_element.append(slt_tree[1].tag)
                    formula_next = slt_tree[1].active_children()
                    return cls.parse_tree(formula_next, formula_element)

class SympyObjectConverter:

    def __init__(self, var_dic, calculation_info):
        self._var_dic = var_dic
        self._calculation_info = calculation_info
        list_number = list(filter(lambda x: type(x) is list, calculation_info))
        if list_number:
            self.has_list = True
        else:
            self.has_list = False

    def get_sympy_object(self):

        calculation_info_copy = copy.deepcopy(self._calculation_info)

        if not self.has_list:
            sympy_object = self.make_simple_formula(calculation_info_copy, self._var_dic)
            return sympy_object

        else:
            # 複雑な式を[object1, object2, calculation]形式で返す
            calculation_info_list = list(filter(lambda x: type(x) == list, calculation_info_copy))

            #'diff'により変数が関数として再定義される可能性がある
            for lst in calculation_info_list:
                idx = calculation_info_copy.index(lst)
                calculation_info_copy[idx] = self.deal_with_list(lst=lst, var_dic=self._var_dic)

            #リストの情報を展開した後に，それをもう一度make_simple_formula関数に通す
            sympy_object = self.make_simple_formula(calculation_info_copy, self._var_dic)

            return sympy_object

    @classmethod
    def make_simple_formula(cls, calculation_info, var_dic):

        try:
            if '*' in calculation_info:
                print('* is already used')
            else:
                calculation_info = cls.add_multiple_operator(calculation_info)

            for idx, element in enumerate(calculation_info):

                if type(element) is str and 'N!' in element:
                    number = element.split('!')[1]
                    if number.isdigit():
                        calculation_info[idx] = int(element.split('!')[1])
                    else:
                        calculation_info[idx] = float(element.split('!')[1])

                elif element in var_dic:
                    calculation_info[idx] = var_dic[element]

            #mutiple division first
            calculation_info = cls.outter_calculation(calculation_info)

            formula = calculation_info[0]  # 数式の一番目に来るのが変数か、数字であると仮定する

            for idx, element in enumerate(calculation_info):

                if element == '+':
                    formula += calculation_info[idx+1]

                elif element == '-':
                    formula -= calculation_info[idx+1]

            result = formula

        #sympy object がきた時にそのまま返す
        except:
            result = calculation_info

        return result

    @classmethod
    def add_multiple_operator(cls, formula_info):
        if len(formula_info) == 1:
            return formula_info
        elif not formula_info:
            print('nothing')
        else:
            for idx, element in enumerate(formula_info):
                if idx == len(formula_info) - 1:
                    return formula_info
                element_n = formula_info[idx + 1]
                if element not in ['+', '-', '*', r'/'] and element_n not in ['+', '-', '*', r'/']:  #演算子でなければ、数字あるいは変数である
                    formula_info.insert(idx+1, '*')
                    break
            return cls.add_multiple_operator(formula_info)

    @classmethod
    def outter_calculation(cls, info):

        if info[0] in ['+', '-']:
            info.insert(0, 0)

        def _inner_calculation(term):
            result = term[0]
            for idx, elem in enumerate(term):
                if elem == '*':
                    result *= term[idx + 1]
                elif elem == '/':
                    result /= term[idx + 1]
            return result

        calculation_info = []
        term = []
        for elem in info:
            if elem not in ['+', '-']:
                term.append(elem)
            else:
                value = _inner_calculation(term)
                term = []
                calculation_info.append(value)
                calculation_info.append(elem)

        value = _inner_calculation(term)
        calculation_info.append(value)

        return calculation_info

    @classmethod
    def deal_with_list(cls, lst, var_dic):

        if len(lst) == 3:

            if lst[2] == 'within':
                calculation_info_inside = lst[0]
                sympy_object = cls(var_dic=var_dic,
                                   calculation_info=calculation_info_inside).get_sympy_object()
                return sympy_object

            elif lst[2] == 'frac':

                calculation_info_over = lst[0]
                calculation_info_under = lst[1]

                sympy_object_over = cls(var_dic=var_dic, calculation_info=calculation_info_over).get_sympy_object()
                sympy_object_under = cls(var_dic=var_dic, calculation_info=calculation_info_under).get_sympy_object()

                if type(sympy_object_over) == int and type(sympy_object_under) == int:
                    return sy.Rational(sympy_object_over, sympy_object_under)
                else:
                    return sympy_object_over/sympy_object_under

            elif lst[2] == 'exp':

                calculation_info_below = lst[0]
                calculation_info_above = lst[1]
                sympy_object_below = cls(var_dic=var_dic, calculation_info=calculation_info_below).get_sympy_object()
                sympy_object_above = cls(var_dic=var_dic, calculation_info=calculation_info_above).get_sympy_object()

                return sympy_object_below ** sympy_object_above

            elif lst[2] == 'root':

                calculation_info_inside = lst[0]
                calculation_info_pre_above = lst[1]

                if lst[1] is not None:
                   sympy_object_pre_above = cls(var_dic=var_dic,
                                                calculation_info=calculation_info_pre_above).get_sympy_object()
                else:
                    sympy_object_pre_above = 2

                sympy_object_inside = cls(var_dic=var_dic,
                                          calculation_info=calculation_info_inside).get_sympy_object()
                if type(sympy_object_pre_above) is int:
                    return sympy_object_inside**sy.Rational(1, sympy_object_pre_above)
                else:
                    return sympy_object_inside**(1/sympy_object_pre_above)

            elif lst[2] == 'log':

                calculation_info_below = lst[0]
                calculation_info_logarithm = lst[1]

                if calculation_info_below is not None:
                    sympy_object_below = cls(var_dic=var_dic, calculation_info=calculation_info_below).get_sympy_object()
                else:
                    sympy_object_below = sy.E

                sympy_object_logarithm = cls(var_dic=var_dic,
                                             calculation_info=calculation_info_logarithm).get_sympy_object()

                return sy.log(sympy_object_below, sympy_object_logarithm)

            elif lst[2] in ['sin', 'cos', 'tan', 'sec', 'cosec', 'cotan', 'asin', 'acos', 'atan']:

                calculation_info_inside = lst[0]

                sympy_object_inside = cls(var_dic=var_dic,
                                          calculation_info=calculation_info_inside).get_sympy_object()

                if lst[2] == 'sin':
                    return sy.sin(sympy_object_inside)

                elif lst[2] == 'cos':
                    return sy.cos(sympy_object_inside)

                elif lst[2] == 'tan':
                    return sy.tan(sympy_object_inside)

                elif lst[2] == 'cosec':
                    return 1 / sy.sin(sympy_object_inside)

                elif lst[2] == 'sec':
                    return 1 / sy.cos(sympy_object_inside)

                elif lst[2] == 'cotan':
                    return 1 / sy.tan(sympy_object_inside)

                elif lst[2] == 'asin':
                    return sy.asin(sympy_object_inside)

                elif lst[2] == 'acos':
                    return sy.acos(sympy_object_inside)

                elif lst[2] == 'atan':
                    return sy.atan(sympy_object_inside)

            elif lst[2] == 'diff':
                calculation_info_over = lst[0]
                calculation_info_under = lst[1]
                sympy_object_above = cls(var_dic=var_dic, calculation_info=calculation_info_over).get_sympy_object()
                sympy_object_below = cls(var_dic=var_dic, calculation_info=calculation_info_under).get_sympy_object()
                return sy.diff(sympy_object_above, sympy_object_below)

        #lstの長さが3でければ5と仮定する
        else:
            if lst[-1] == 'sum':
                calculation_info_var_for_sum = lst[0]
                calculation_info_lower_limit = lst[1]
                calculation_info_upper_limit = lst[2]
                calculation_info_within = lst[3]
                sympy_object_var_for_sum = cls(var_dic=var_dic, calculation_info=calculation_info_var_for_sum).get_sympy_object()
                sympy_object_lower_limit = cls(var_dic=var_dic, calculation_info=calculation_info_lower_limit).get_sympy_object()
                sympy_object_upper_limit = cls(var_dic=var_dic, calculation_info=calculation_info_upper_limit).get_sympy_object()
                sympy_object_info_within = cls(var_dic=var_dic, calculation_info=calculation_info_within).get_sympy_object()
                return sy.summation(sympy_object_info_within, (sympy_object_var_for_sum, sympy_object_lower_limit, sympy_object_upper_limit))





