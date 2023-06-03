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


TEST_DATA_FOLDER = "./test_data/test_data_latex"
EQ_GROUP_PAIR_LIST = (
    # Equivalent pair
    ("simple01_1", "simple01_2", 1),
    ("simple03_1", "simple03_2", 1),
    ("simple05_1", "simple05_2", 1),
    ("massbalance01_1", "massbalance01_2", 1),
    ("blending01_1", "blending01_2", 1),
    ("liquid_storage01_1", "liquid_storage01_2", 1),
    ("CSTR_1storder01_1", "CSTR_1storder01_2", 1),
    ("CSTR_1storder01_2", "CSTR_1storder01_3", 1),
    ("CSTR_1storder02_1", "CSTR_1storder02_2", 1),
    ("CSTR_1storder02_2", "CSTR_1storder02_3", 1),
    ("CSTR_1storder02_1", "CSTR_1storder02_3", 1),
    ("CSTR_2ndorder01_1", "CSTR_2ndorder01_2", 1),
    ("CSTR_2ndorder01_2", "CSTR_2ndorder01_3", 1),
    ("CSTR_2ndorder01_1", "CSTR_2ndorder01_3", 1),
    ("three_absorber01_1", "three_absorber01_3", 1),
    ("two_stirred_tank01_1", "two_stirred_tank01_2", 1),
    ("two_stirred_tank02_1", "two_stirred_tank02_2", 1),
    ("three_stirred_tank01_1", "three_stirred_tank01_2", 1),
    ("three_stirred_tank02_1", "three_stirred_tank02_2", 1),
    ("elec_heat_tank01_1", "elec_heat_tank01_2", 1),
    ("elec_heat_tank01_2", "elec_heat_tank01_3", 1),
    ("elec_heat_tank01_1", "elec_heat_tank01_3", 1),
    ("batch_reactor01_1", "batch_reactor01_2", 1),
    ("biodiesel01_1_1", "biodiesel01_2_1", 1),
    ("biodiesel02_1_1", "biodiesel02_2_1", 1),
    # Inequivalent pair
    ("simple01_1", "simple02_1", 0),
    ("simple03_1", "simple04_1", 0),
    ("simple05_1", "simple06_1", 0),
    ("massbalance01_1", "massbalance02_1", 0),
    ("blending01_1", "massbalance01_1", 0),
    ("CSTR_1storder01_1", "CSTR_1storder02_1", 0),
    ("CSTR_1storder01_1", "CSTR_2ndorder01_1", 0),
    ("CSTR_1storder01_2", "CSTR_1storder02_2", 0),
    ("CSTR_1storder01_2", "CSTR_2ndorder01_2", 0),
    ("CSTR_1storder01_3", "CSTR_1storder02_3", 0),
    ("CSTR_1storder01_3", "CSTR_2ndorder01_3", 0),
    ("CSTR_1storder02_1", "CSTR_2ndorder01_1", 0),
    ("CSTR_1storder02_2", "CSTR_2ndorder01_2", 0),
    ("CSTR_1storder02_3", "CSTR_2ndorder01_3", 0),
    ("two_stirred_tank01_1", "two_stirred_tank02_1", 0),
    ("two_stirred_tank01_1", "two_stirred_tank02_2", 0),
    ("two_stirred_tank01_2", "two_stirred_tank02_1", 0),
    ("two_stirred_tank01_2", "two_stirred_tank02_2", 0),
    ("three_stirred_tank01_1", "three_stirred_tank02_1", 0),
    ("three_stirred_tank01_1", "three_stirred_tank02_2", 0),
    ("three_stirred_tank01_2", "three_stirred_tank02_1", 0),
    ("three_stirred_tank01_2", "three_stirred_tank02_2", 0),
    ("biodiesel01_1_1", "biodiesel02_1_1", 0),
    ("biodiesel01_1_1", "biodiesel02_2_1", 0),
    ("biodiesel01_2_1", "biodiesel02_2_1", 0),
)


def main():
    """Test all cases.
    About eq_group_label:
        **processname{type}_{format}**
        type: equivalent two equation groups are the same type
        format: written format of equation groups
    """
    for i, (eq_group1_label, eq_group2_label, answer) in enumerate(
        EQ_GROUP_PAIR_LIST, start=1
    ):

        eq_group_path_1 = f"{TEST_DATA_FOLDER}/{eq_group1_label}.tex"
        eq_group_path_2 = f"{TEST_DATA_FOLDER}/{eq_group2_label}.tex"

        eq_group_obj_1 = extract_eq_group_from_tex(eq_group_path_1)
        eq_group_obj_2 = extract_eq_group_from_tex(eq_group_path_2)

        judgment_result = eq_group_obj_1 == eq_group_obj_2

        if judgment_result == bool(answer):
            print(f"Case {i} PASSED. {eq_group1_label}, {eq_group2_label}")
        else:
            print(f"Case {i} FAILED. {eq_group1_label}, {eq_group2_label}")


if __name__ == "__main__":
    main()
