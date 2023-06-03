from dae_equiv_judge.latex_to_eq_group import latex_to_eq_group


def extract_eq_group_from_tex(texfilepath):
    latex_eq_list = []
    with open(texfilepath, "r") as f:
        doc_tex = f.read()
    for line_ in doc_tex.split("\n"):
        if "=" in line_:
            latex_eq_list.append(line_)

    eq_group = latex_to_eq_group(latex_eq_list)

    return eq_group


def main():

    eq_group_path_1 = "./test_data/test_data_latex/batch_reactor01_1.tex"
    eq_group_path_2 = "./test_data/test_data_latex/batch_reactor01_2.tex"
    print(eq_group_path_1)
    print(eq_group_path_2)

    eq_group_obj_1 = extract_eq_group_from_tex(eq_group_path_1)
    eq_group_obj_2 = extract_eq_group_from_tex(eq_group_path_2)

    is_same = eq_group_obj_1 == eq_group_obj_2

    print(is_same)


if __name__ == "__main__":
    main()
