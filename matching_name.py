def matching_name(truth_name, name):
    rt_truth_name = root1(truth_name)
    rt_match_name = root1(name)
    if len(name.strip().replace('.', '')) <= 1 or len(
            name.strip().replace('(', '').replace(')', '').replace('-', '')) > 7:
        # delete single letter and too long name
        return "DEL"
    # if is_contain_chinese(name):  # delete name has chinese
    #     return "DEL"
    # if is_number(root2(name)):  # delete name only has numbers
    #     return "DEL"
    my_re = re.compile(r'[A-Za-z]', re.S)
    res = re.findall(my_re, name)
    if not len(res):  # delete name not has letter
        return "DEL"
    if rt_match_name == rt_truth_name or root2(rt_match_name) == root2(rt_truth_name):
        return "OK"
    else:
        return "WRONG"
