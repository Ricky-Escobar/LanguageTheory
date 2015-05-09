from itertools import product


def tup2string(tup):
    s = ""
    for c in tup:
        s += c
    return s


def copy(lst):
    return [sub[:] for sub in lst]


class Automaton(object):
    def __init__(self, alphabet=set('ab'), final=None, lambda_transitions=False):
        self.lambda_transitions = lambda_transitions
        self.alphabet = alphabet | {''} if lambda_transitions else alphabet
        self.delta = [{c: set() for c in self.alphabet}]
        self.final = set() if final is None else final

    def put(self, from_state, a, *to_states):
        self.delta += [{c: set() for c in self.alphabet} for _ in
                       range(len(self.delta), max(from_state, max(to_states)) + 1)]
        self.delta[from_state][a].update(set(to_states))

    def __contains__(self, string):
        return self._process(string)

    def _t(self, state, a):
        states = set()
        for state1 in self.closure(state):
            for state2 in self.delta[state1][a]:
                states.update(self.closure(state2))
        return states

    def _process(self, string, state=0):
        if string == "":
            return not self.closure(state).isdisjoint(self.final)
        for target in self._t(state, string[0]):
            if self._process(string[1:], target):
                return True
        return False

    def is_dfa(self):
        for state in self.delta:
            for target in state.values():
                if len(target) != 1:
                    return False
        return True

    def to_dfa(self):
        new = Automaton(self.alphabet - {''})
        ndx2subset = {0: frozenset(self.closure(0))}
        subset2ndx = {ndx2subset[0]: 0}
        left = [(0, a) for a in new.alphabet]
        while left:
            from_state_ndx, a = left.pop(0)
            to_state_set = set()
            for state in ndx2subset[from_state_ndx]:
                to_state_set.update(self._t(state, a))
            to_state_set = frozenset(to_state_set)
            try:
                to_state_ndx = subset2ndx[to_state_set]
            except KeyError:
                to_state_ndx = len(ndx2subset)
                subset2ndx[to_state_set] = to_state_ndx
                ndx2subset[to_state_ndx] = to_state_set
                left += [(to_state_ndx, c) for c in new.alphabet]
            new.put(from_state_ndx, a, to_state_ndx)
        new.final = {ndx for ndx, subset in ndx2subset.items() if not subset.isdisjoint(self.final)}
        return new, ndx2subset

    def __str__(self):
        return self.__str()

    def __str(self, fmt=False):
        dfa = self.is_dfa()
        s = "final: " + str({(float(k) if fmt else k) for k in self.final}) + "\n"
        for i in range(len(self.delta)):
            s += str(i) + ": "
            for a, states in self.delta[i].items():
                s += a + ":"
                if not dfa:
                    s += '{'
                s += ",".join(str(state) for state in states)
                if not dfa:
                    s += '}'
                s += "  "
            s += '\n'
        return s

    def print_fmt(self, dct):
        p = self.__str(True)
        for i in dct:
            p = p.replace(str(i) + ".0", str(dct[i]))
            p = p.replace(":" + str(i), ": " + str(dct[i])).replace(str(i) + ":", str(dct[i]) + ":")
        print p.replace("set([", "{").replace("])", "}").replace("frozen", "")

    def closure(self, state, seen=set()):
        if self.lambda_transitions:
            states = {state}
            for target in self.delta[state][""]:
                if target not in seen:
                    states |= self.closure(target, seen | states)
            return states
        else:
            return {state}

    def __eq__(self, other):
        return self.language(7) == other.language(7)

    def language(self, length=5):
        return sorted(filter(lambda s: s in self,
                             {tup2string(tup) for i in range(length + 1) for tup in product(self.alphabet, repeat=i)}))

    # no lambda
    def regex(self):
        mat = [[None for _ in range(len(self.delta))] for _ in range(len(self.delta))]
        for src in range(len(self.delta)):
            for c in self.delta[src]:
                for dest in self.delta[src][c]:
                    mat[src][dest] = union(mat[src][dest], c)
        return ExpressionGraph(self.alphabet, list(self.final), mat).regex()


class ExpressionGraph(object):
    def __init__(self,  alphabet, final=None, init_mat=None):
        self.mat = copy(init_mat) if init_mat is not None else [[None]]
        self.final = final if final is not None else [0]
        self.alphabet = alphabet

    def regex(self):
        ret = None
        for state in self.final:
            ret = union(ret, ExpressionGraph(self.alphabet, [state], self.mat).regex_1_final())
        for c in self.alphabet:
            ret = ret.replace(c + c + "*", c + "+").replace(c + "*" + c, c + "+")
        return ret

    def regex_1_final(self):
        mat = self.mat
        final = self.final[0]
        for i in range(len(mat)):
            if i != final and i != 0:
                for j in range(len(mat)):
                    if j != i:
                        for k in range(len(mat)):
                            if k != i:
                                mat[j][k] = union(mat[j][k], concat(concat(mat[j][i], star(mat[i][i])), mat[i][k]))
                for j in range(len(mat)):
                    mat[i][j] = None
                    mat[j][i] = None
        if final == 0:
            return star(mat[0][0])
        else:
            u, v, w, x = mat[0][0], mat[0][final], mat[final][final], mat[final][0]
            return concat(concat(star(u), v), star(union(w, concat(concat(x, star(u)), v))))


def concat(u, v):
    if u is None or v is None:
        return None
    if u == "":
        return "" + v
    if v == "":
        return "" + u
    u_parens = union_outside_parens(u)
    v_parens = union_outside_parens(v)
    return "(" * u_parens + u + ")" * u_parens + "(" * v_parens + v + ")" * v_parens


def star(s):
    if s is None or s == "":
        return ""
    if len(s) == 1:
        return s + "*"
    return "(" + s + ")*"


def union(s, t):
    if s is None and t is None:
        return None
    if s is None:
        return "" + t
    if t is None or s == t:
        return "" + s
    if s == "":
        return "''|" + t
    if t == "":
        return s + "|''"
    return s + "|" + t


def union_outside_parens(s):
    parens = 0
    for c in s:
        if parens == 0 and c == '|':
            return True
        elif c == '(':
            parens += 1
        elif c == ')':
            parens -= 1
    return False


def test4():
    m = Automaton(final={1, 2})
    m.put(0, 'a', 1)
    m.put(1, 'b', 0, 2)
    m.put(2, 'a', 1, 3)
    m.put(3, 'b', 2)

    print m.regex()


def test3():
    m = Automaton(final={2})
    m.put(0, 'a', 0, 2)
    m.put(0, 'b', 1)
    m.put(1, 'a', 0)
    m.put(1, 'b', 1, 2)

    print m.to_dfa()[0]


def test2():
    m = Automaton(final={1})
    m.put(0, 'a', 1)
    m.put(0, 'b', 1)
    m.put(1, 'a', 1)
    m.put(1, 'b', 2)
    m.put(2, 'b', 2)
    m.put(2, 'a', 1)

    print m.regex()


def test1():
    m = Automaton(set('ab'), {1})
    m.put(0, 'a', 1, 3)
    m.put(0, 'b', 0)
    m.put(1, 'a', 0)
    m.put(1, 'b', 2)
    m.put(3, 'b', 2)
    m.put(2, 'a', 3)
    m.put(2, 'b', 1, 2)

    print m.regex()

if __name__ == '__main__':
    test4()
