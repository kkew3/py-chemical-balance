import typing as ty
import re
import enum

import numpy as np


def isdigitdot(s: str) -> bool:
    return re.fullmatch(r'[0-9.]+', s)


def preprocesseq(line: str) -> str:
    """
    >>> preprocesseq('A')
    '((A))'
    >>> preprocesseq('A2')
    '((A(2)))'
    >>> preprocesseq('AB')
    '((A)(B))'
    >>> preprocesseq('A2B')
    '((A(2))(B))'
    >>> preprocesseq('A(A2B)3')
    '((A)(((A(2))(B))(3)))'
    >>> preprocesseq('A2(AB)3')
    '((A(2))(((A)(B))(3)))'
    >>> preprocesseq('Ah1(AhB4)2B3')
    '((Ah(1))(((Ah)(B(4)))(2))(B(3)))'
    >>> preprocesseq('NH3 + O2 = H2NO3')
    '((N)(H(3)))+((O(2)))=((H(2))(N)(O(3)))'
    """

    # Match the rules from top to bottom. If no rule is matched, then current
    # character triggers ValueError.
    #
    # First column:
    #   callable matches x such that callable(x) is True
    #   str matches x such that x in str
    #   None matches the beginning
    # Second column:
    #   callable matches x such that callable(x) is True
    #   str matches x such that x in str
    #   None matches the end
    # Third column:
    #   str means append buffer with str and current character
    #   None means ValueError
    buf_ext_rules = [
        (str.isupper, str.isupper, ')('),
        (str.isupper, str.islower, ''),
        (str.isupper, isdigitdot, '('),
        (str.isupper, '(', ')('),
        (str.isupper, ')', ')'),
        (str.isupper, '+=', '))'),
        (str.isupper, None, '))'),
        (str.islower, str.isupper, ')('),
        (str.islower, str.islower, ''),
        (str.islower, isdigitdot, '('),
        (str.islower, '(', ')('),
        (str.islower, ')', ')'),
        (str.islower, '+=', '))'),
        (str.islower, None, '))'),
        (isdigitdot, str.isupper, '))('),
        (isdigitdot, str.islower, None),
        (isdigitdot, isdigitdot, ''),
        (isdigitdot, '(', '))('),
        (isdigitdot, ')', '))'),
        (isdigitdot, '+=', ')))'),
        (isdigitdot, None, ')))'),
        ('(', str.isupper, '('),
        ('(', str.islower, None),
        ('(', isdigitdot, None),
        ('(', '()', ''),
        ('(', '+=', None),
        ('(', None, None),
        (')', str.isupper, '('),
        (')', str.islower, None),
        (')', isdigitdot, '('),
        (')', '()', ''),
        (')', '+=', '))'),
        (')', None, '))'),
        ('+=', str.isupper, '(('),
        ('+=', str.islower, None),
        ('+=', isdigitdot, None),
        ('+=', '(', '(('),
        ('+=', ')', None),
        ('+=', '+=', None),
        ('+=', None, None),
        (None, str.isupper, '(('),
        (None, str.islower, None),
        (None, isdigitdot, None),
        (None, '(', '(('),
        (None, ')', None),
        (None, '+=', None),
        (None, None, None),
    ]

    buf = []
    i = 0
    n = len(line)

    while i <= n:
        if i < n and line[i].isspace():
            i += 1
            continue
        for pat1, pat2, cnt in buf_ext_rules:
            if pat1 is None:
                pat1_matched = not buf
            elif callable(pat1):
                pat1_matched = pat1(buf[-1]) if buf else False
            else:
                pat1_matched = buf[-1] in pat1 if buf else False
            if pat2 is None:
                pat2_matched = i == n
            elif callable(pat2):
                pat2_matched = pat2(line[i]) if i < n else False
            else:
                pat2_matched = line[i] in pat2 if i < n else False
            if pat1_matched and pat2_matched:
                if cnt is None:
                    raise ValueError(
                        'illegal character at position {}'.format(i))
                buf.append(cnt)
                if i < n:
                    buf.append(line[i])
                break
        else:
            raise ValueError('illegal character at position {}'.format(i))
        i += 1
    return ''.join(buf)


def parseeq(line: str) -> ty.List[ty.Dict[str, float]]:
    class States(enum.Enum):
        NEW = 1
        PUSH = 2
        MERGE = 3
        WRITE = 4

    stack: ty.Optional[ty.List[ty.Union[str, ty.Dict[str, float]]]] = None
    results: ty.List[ty.Dict[str, float]] = []
    side: ty.Literal[1., -1.] = 1.
    state: ty.Optional[States] = None
    inputs = [None] + list(line)

    # Jumplist goes from top to bottom. If none matches, error will be raised.
    #
    # First column: current state
    # Second column: current input, where:
    #   str matches x such that x in str
    #   None matches None
    #   True matches all
    # Third column: next state, or `None` to signify invalid jump
    jumplist = [
        (None, None, States.NEW),
        (States.NEW, '(', States.PUSH),
        (States.PUSH, '(', States.PUSH),
        (States.PUSH, ')', States.MERGE),
        (States.PUSH, '+=', None),
        (States.PUSH, True, States.WRITE),
        (States.WRITE, '(', States.PUSH),
        (States.WRITE, ')', States.MERGE),
        (States.WRITE, '+=', None),
        (States.WRITE, True, States.WRITE),
        (States.MERGE, '(', States.PUSH),
        (States.MERGE, ')', States.MERGE),
        (States.MERGE, '+=', States.NEW),
    ]

    def action_new(_i, _x):
        nonlocal stack
        nonlocal side
        if _x == '=':
            side = -1.
            if stack:
                raise RuntimeError('error occurs at position {}'.format(_i))
        elif _x == '+':
            if stack:
                raise RuntimeError('error occurs at position {}'.format(_i))
        elif _x is None:
            stack = []
        else:
            raise RuntimeError('error occurs at position {}'.format(_i))

    def action_push(_i, _x):
        if _x != '(':
            raise RuntimeError('error occurs at position {}'.format(_i))
        stack.append({})

    # pylint: disable=unsubscriptable-object
    def action_write(_i, _x):
        if isinstance(stack[-1], dict):
            if stack[-1]:
                raise RuntimeError('error occurs at position {}'.format(_i))
            stack[-1] = _x
        else:
            stack[-1] += _x

    # pylint: disable=unsubscriptable-object
    def action_merge(_i, _x):
        if _x != ')':
            raise RuntimeError('error occurs at position {}'.format(_i))
        if len(stack) == 1 and isinstance(stack[-1], dict):
            results.append(stack.pop())
        elif (len(stack) >= 2 and isinstance(stack[-1], str)
              and isinstance(stack[-2], str) and isdigitdot(stack[-1])
              and stack[-2].isalpha()):
            num = float(stack.pop())
            stack[-1] = {stack[-1]: num * side}
        elif (len(stack) >= 2 and isinstance(stack[-1], str)
              and isinstance(stack[-2], dict)):
            a = stack.pop()
            if isdigitdot(a):
                a = float(a)
                for k in stack[-1]:
                    stack[-1][k] *= a
            else:
                if a not in stack[-1]:
                    stack[-1][a] = 0
                stack[-1][a] += side
        elif (len(stack) >= 2 and isinstance(stack[-1], dict)
              and isinstance(stack[-2], dict)):
            dct = stack.pop()
            for k, v in dct.items():
                if k not in stack[-1]:
                    stack[-1][k] = 0
                stack[-1][k] += v
        else:
            raise RuntimeError('error occurs at position {}'.format(_i))

    actionlist = {
        States.NEW: action_new,
        States.PUSH: action_push,
        States.WRITE: action_write,
        States.MERGE: action_merge,
    }

    for i, x in enumerate(inputs):
        # state transition
        for state_pat, input_pat, next_state in jumplist:
            state_pat_matched = state is state_pat
            if input_pat is None:
                input_pat_matched = x is input_pat
            elif input_pat is True:
                input_pat_matched = True
            else:
                input_pat_matched = x in input_pat
            if state_pat_matched and input_pat_matched:
                state = next_state
                break
        else:
            raise RuntimeError('error occurs at position {}'.format(i))

        actionlist[state](i, x)

    return results


def form_coef_mat(parse_results: ty.List[ty.Dict[str, float]]) -> np.ndarray:
    all_ele: ty.Set[str] = set()
    for d in parse_results:
        all_ele.update(d)
    A = []
    for e in all_ele:
        row = []
        for d in parse_results:
            row.append(d.get(e, 0.0))
        A.append(row)
    A = np.array(A)
    return A
