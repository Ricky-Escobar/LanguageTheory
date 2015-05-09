from random import choice


def get_rule_cmp(rules):
    def rule_cmp(u, v):
        var_count_u, var_count_v = 0, 0
        for c in u:
            if c in rules:
                var_count_u += 1
        for c in v:
            if c in rules:
                var_count_v += 1
        if var_count_u == var_count_v:
            return len(u) - len(v)
        else:
            return var_count_u - var_count_v
    return rule_cmp


def parse(*rule_strs):
    rules = {}
    for s in rule_strs:
        var_rules = s.split('|')
        var, first = tuple(var_rules[0].split("->"))
        rules[var] = [first] + var_rules[1:]
    return rules


def cfg(*rule_strs):
    rules = parse(*rule_strs)
    s = 'S'
    var = True
    while var:
        var = False
        for i in range(len(s)):
            if s[i] in rules:
                var = True
                s = s[:i] + choice(rules[s[i]]) + s[i+1:]
                break
    return s


def cfg2(max_len=8, *rule_strs):
    seen = set()
    dct = parse(*rule_strs)
    for var, rule_list in dct.items():
        dct[var] = sorted(rule_list, cmp=get_rule_cmp(dct))
    print dct

    def cfg_rec(start):
        if len(start) <= max_len:
            if start not in seen:
                seen.add(start)
            if not any([c in dct for c in start]):
                yield start
            else:
                for i, c in enumerate(start):
                    if c in dct:
                        for repl in dct[c]:
                            for x in cfg_rec(start[:i] + repl + start[i+1:]):
                                yield x

    for s in cfg_rec('S'):
        yield s


def main():
    for s in cfg2(10, "S->aS|bB|cC|", "B->bB|cC|", "C->cC|"):
        print s

if __name__ == "__main__":
    main()