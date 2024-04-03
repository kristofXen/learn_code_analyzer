# write your code here
# import os
from typing import Protocol
from dataclasses import dataclass
import os
import sys
import ast


@dataclass
class StyleIssue:
    line_nr: int
    code: str
    message: str
    sc_url: str = ''


# The different checks #
class Check(Protocol):
    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        ...


class CheckLineLength:
    def __init__(self, max_line_length: int = 79,
                 code: str='S001',
                 message: str='Too long'):
        self.max_line_length = max_line_length
        self.code = code
        self.message = message

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_list: list[StyleIssue] = []
        for i, line in enumerate(sc):
            if len(line) <= self.max_line_length + 1:  # +1 for \n char
                pass
            else:
                style_issue = StyleIssue(i, self.code, self.message, url)
                check_res_list.append(style_issue)
        return check_res_list


class CheckIndentation:
    def __init__(self, nr_of_indents: int = 4,
                 code: str = 'S002',
                 message: str = 'Indentation is not a multiple of four'):
        self.nr_of_indents = nr_of_indents
        self.code = code
        self.message = message

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_list: list[StyleIssue] = []
        for i, line in enumerate(sc):
            if self._count_leading_spaces(line) % self.nr_of_indents != 0:
                check_res_list.append(StyleIssue(
                    i, self.code, self.message, url))
        return check_res_list

    def _count_leading_spaces(self, line: str) -> int:
        return len(line) - len(line.lstrip(' '))


class CheckSemicolon:
    def __init__(self, code: str = 'S003',
                 message: str = 'Unnecessary semicolon'):
        self.code = code
        self.message = message

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_list: list[StyleIssue] = []
        for i, line in enumerate(sc):
            spl_st = line.split('#')
            sc_line = spl_st[0]
            for j, char in enumerate(sc_line):
                if char == ';' and not is_part_of_string_var(sc_line, j):
                    check_res_list.append(
                        StyleIssue(i, self.code, self.message, url)
                    )
                    break
        return check_res_list

class CheckInlineComment:
    def __init__(self, min_nr_of_spaces_required: int = 2,
                 code: str = 'S004',
                 message: str = 'At least two spaces required before '
                                'inline comments'):
        self.code = code
        self.message = message
        self.min_nr_of_spaces_required = min_nr_of_spaces_required

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_list: list[StyleIssue] = []
        for i, line in enumerate(sc):
            if line.startswith('#'):
                pass
            else:
                spl_st = line.split('#')
                if len(spl_st) == 1:
                    pass  # no comments made
                else:
                    if spl_st[0][-2:] != ' '*self.min_nr_of_spaces_required:
                        check_res_list.append(
                            StyleIssue(i, self.code, self.message, url)
                        )
        return check_res_list


class CheckTodo:
    def __init__(self, code: str = 'S005',
                 message: str = 'TODO found'):
        self.code = code
        self.message = message

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_list: list[StyleIssue] = []
        for i, line in enumerate(sc):
            spl_st = line.split('#')
            if len(spl_st) == 1:
                pass  # no comments made
            else:
                comment = spl_st[-1]
                if 'todo' in comment.lower():
                    check_res_list.append(
                        StyleIssue(i, self.code, self.message, url)
                    )
        return check_res_list


class CheckBlankLines:
    def __init__(self, code: str = 'S006',
                 message: str = 'More than two blank lines used before '
                                'this line'):
        self.code = code
        self.message = message

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_list: list[StyleIssue] = []
        for i, line in enumerate(sc):
            sc_line = line.split('#')[0]
            if i < 3:
                pass
            else:
                if sc_line.rstrip() != '' \
                    and sc[i-1].rstrip() == '' \
                        and sc[i-2].rstrip() == '' \
                            and sc[i-3].rstrip() == '':
                    check_res_list.append(
                        StyleIssue(i, self.code, self.message, url)
                    )
        return check_res_list


class CheckSpaceAfterConstruction:
    def __init__(self, code: str = 'S007',
                 message: str = "Too many spaces after 'class'",
                 constructions: list[str] = ['class', 'def']):
        self.code = code
        self.message = message
        self.constructions = constructions

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_lst: list[StyleIssue] = []
        for i, line in enumerate(sc):
            sc_line = line.split('#')[0]
            for constr in self.constructions:
                if constr in sc_line:
                    try:
                        start_indx = sc_line.find(constr)
                        if sc_line[start_indx + len(constr)] == ' ' \
                           and sc_line[start_indx + len(constr) + 1] != ' ':
                            pass
                        else:
                            check_res_lst.append(
                                StyleIssue(i, self.code, self.message, url)
                            )
                    except IndexError:
                        check_res_lst.append(
                            StyleIssue(i, self.code, self.message, url)
                        )
        return check_res_lst


class CheckClassNames:
    def __init__(self, code: str = 'S008',
                 message: str = "Class name '' should use CamelCase",
                 msg_insertion_point_indx: int = 12):
        self.code = code
        self.messeage = message
        self.msg_insertion_point_indx = msg_insertion_point_indx

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_lst: list[StyleIssue] = []
        for i, line in enumerate(sc):
            sc_line = line.split('#')[0]
            sc_words = sc_line.split()
            if 'class' in sc_words:
                class_word_index = sc_words.index('class')
                try:
                    next_word = sc_words[class_word_index + 1].split(':')[0]
                    if next_word[0].isupper() and next_word[1].islower():
                        pass
                    else:
                        class_name = next_word.split('(')[0]
                        msg = self.messeage[:self.msg_insertion_point_indx] \
                              + class_name \
                              + self.messeage[self.msg_insertion_point_indx:]
                        check_res_lst.append(
                            StyleIssue(i, self.code, msg, url)
                        )
                    if '(' in next_word:
                        inherit_class_name = next_word.split('(')[-1]
                        inherit_class_name = inherit_class_name.split(')')[0]
                        if inherit_class_name[0].isupper() and inherit_class_name[1].islower():
                            pass
                        else:
                            msg = self.messeage[:self.msg_insertion_point_indx] \
                                  + inherit_class_name \
                                  + self.messeage[
                                    self.msg_insertion_point_indx:]
                            check_res_lst.append(
                                StyleIssue(i, self.code, msg, url)
                            )

                except IndexError:
                    msg = self.messeage[:self.msg_insertion_point_indx] \
                          + '' \
                          + self.messeage[self.msg_insertion_point_indx:]
                    check_res_lst.append(
                        StyleIssue(i, self.code, msg, url)
                    )

        return check_res_lst


class CheckFunctionNames:
    def __init__(self, code: str = 'S009',
                 message: str = "Function name '' should use snake_case",
                 msg_insertion_point_indx: int = 15):
        self.code = code
        self.messeage = message
        self.msg_insertion_point_indx = msg_insertion_point_indx

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_lst: list[StyleIssue] = []
        for i, line in enumerate(sc):
            sc_line = line.split('#')[0]
            sc_words = sc_line.split()

            if 'def' in sc_words:
                def_name_index = sc_words.index('def')
                try:
                    next_word = sc_words[def_name_index + 1].split('(')[0]
                    for part in next_word.split('_'):
                        if part.islower() or part == '':
                            pass
                        else:
                            msg = self.messeage[:self.msg_insertion_point_indx] \
                                  + next_word \
                                  + self.messeage[
                                    self.msg_insertion_point_indx:]
                            check_res_lst.append(
                                StyleIssue(i, self.code, msg, url)
                            )
                            break
                except IndexError:
                    msg = self.messeage[:self.msg_insertion_point_indx] \
                          + '' \
                          + self.messeage[self.msg_insertion_point_indx:]
                    check_res_lst.append(
                        StyleIssue(i, self.code, msg, url)
                    )
        return check_res_lst


class CheckArgNames:
    def __init__(self, code: str = 'S010',
                 message: str = "Argument name '' should be snake_case",
                 msg_insertion_point_indx: int = 15):
        self.code = code
        self.messeage = message
        self.msg_insertion_point_indx = msg_insertion_point_indx
        self.tree = None
        self.args_d_list: list[dict] = None

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_lst: list[StyleIssue] = []
        try:
            self.tree = create_tree_of_code(combine_list_to_sting(sc))
        except IndentationError:
            return check_res_lst

        self.get_arg_name_dict_list()
        for arg_name_d in self.args_d_list:
            for arg_name in arg_name_d['args']:
                for part in arg_name.split('_'):
                    if part.islower() or part == '':
                        pass
                    else:
                        msg = self.messeage[:self.msg_insertion_point_indx] \
                              + arg_name \
                              + self.messeage[
                                self.msg_insertion_point_indx:]
                        check_res_lst.append(
                            StyleIssue(arg_name_d['line_nr']-1, self.code, msg,
                                       url)
                        )
                        break
        return check_res_lst

    def get_arg_name_dict_list(self):
        fdl = CodeLister()
        fdl.visit(self.tree)
        self.args_d_list = fdl.args_d_list


class CheckDefaultValue:
    def __init__(self, code: str = 'S012',
                 message: str = "Default argument value is mutable"):
        self.code = code
        self.messeage = message
        self.tree = None
        self.detaults_d_list: list[dict] = None

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_lst: list[StyleIssue] = []
        try:
            self.tree = create_tree_of_code(combine_list_to_sting(sc))
        except IndentationError:
            return check_res_lst

        self.get_defaults_dict_list()

        for d in self.detaults_d_list:
            for default in d['defaults']:
                if isinstance(default, ast.Constant):
                    pass
                else:
                    check_res_lst.append(
                        StyleIssue(d['line_nr']-1, self.code, self.messeage,
                                   url)
                    )
        return check_res_lst

    def get_defaults_dict_list(self):
        fdl = CodeLister()
        fdl.visit(self.tree)
        self.detaults_d_list = fdl.defaults_d_list


class CheckAssignNames:
    def __init__(self, code: str = 'S011',
                 message: str = "Variable '' in function should be snake_case",
                 msg_insertion_point_indx: int = 10):
        self.code = code
        self.messeage = message
        self.msg_insertion_point_indx = msg_insertion_point_indx
        self.tree = None
        self.assign_d_list: list[dict] = None

    def do_check(self, sc: list[str], url: str) -> list[StyleIssue]:
        check_res_lst: list[StyleIssue] = []
        try:
            self.tree = create_tree_of_code(combine_list_to_sting(sc))
        except IndentationError:
            return check_res_lst

        self.get_assign_dict_list()
        # print(self.assign_d_list)
        for assign_d in self.assign_d_list:
            assign_str = assign_d['assign_in_func_def']
            # print(assign_str)
            for part in assign_str.split('_'):
                if part.islower() or part == '':
                    pass
                else:
                    msg = self.messeage[:self.msg_insertion_point_indx] \
                          + assign_str \
                          + self.messeage[
                            self.msg_insertion_point_indx:]
                    check_res_lst.append(
                        StyleIssue(assign_d['line_nr']-1, self.code, msg,
                                   url)
                    )
                    break
        return check_res_lst

    def get_assign_dict_list(self):
        fdl = CodeLister()
        fdl.visit(self.tree)
        self.assign_d_list = fdl.assign_d_list


# utils #
class CodeLister(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.args_d_list: list[dict] = []
        self.defaults_d_list: list[dict] = []
        self.assign_d_list: list[dict] = []

    def visit_FunctionDef(self, node: ast.FunctionDef, debug=False):
        # use the visit function to find what is needed in the code
        # we need to check the doc to retrieve the arg name
        if debug:
            print(ast.dump(node, indent=4))
        d = dict()
        d['line_nr'] = node.lineno
        d['args'] = [a.arg for a in node.args.args]
        self.args_d_list.append(d)

        d = dict()
        d['line_nr'] = node.lineno
        d['defaults'] = [a for a in node.args.defaults]
        self.defaults_d_list.append(d)
        # self.visit_Assign(node)
        for ch in ast.walk(node):
            if isinstance(ch, ast.Assign):
                if debug:
                    print(ast.dump(ch, indent=4))
                d = dict()
                d['line_nr'] = ch.lineno
                try:
                    d['assign_in_func_def'] = ch.targets[0].id
                except AttributeError:
                    d['assign_in_func_def'] = ch.targets[0].attr

                self.assign_d_list.append(d)
        # self.generic_visit(node)

    # def visit_Assign(self, node: ast.Assign) -> any:
    #     print('assign', ast.dump(node, indent=4))


    # def visit_arguments(self, node: ast.arguments):
    #
    #     print('in arg', ast.dump(node, indent=4))
    #     self.generic_visit(node)


def is_part_of_string_var(line: str, ch_index: int):
    ll = line[:ch_index]
    # rl = line[ch_index+1:]
    l_count_single = ll.count("'")
    l_count_double = ll.count('"')
    if l_count_single % 2 == 1 or l_count_double % 2 == 1:
        return True
    return False


def load_code_file(url: str) -> list[str]:
    with open(url, 'r') as f:
        return f.readlines()


def combine_list_to_sting(lines: list[str]) -> str:
    return ''.join(lines)


def create_tree_of_code(code: str) -> ast.Module:
    return ast.parse(code)


def _sort_list(style_issues_list: list[StyleIssue]) -> list[StyleIssue]:
    return sorted(style_issues_list, key=lambda si: si.line_nr)


def pint_output(style_issues_list: list[StyleIssue]):
    for si in style_issues_list:
        msg = si.sc_url + ': '\
              + 'Line ' \
              + str(si.line_nr+1) + ': ' \
              + si.code + ' ' \
              + si.message
        print(msg)


def find_all_py_files(root_url: str) -> list[str]:
    path_to_py_files = []
    if os.path.isfile(root_url):
        sorted_path_to_py_files = [root_url]
    else:
        for root, dirs, files in os.walk(root_url, topdown=False):
            # print(root, dirs, files)
            for f in files:
                if f.endswith('.py'):
                    fp = os.path.join(root, f)
                    path_to_py_files.append([fp, f])

        # sort
        sorted_paths = sorted(path_to_py_files, key=lambda x: x[1])
        sorted_path_to_py_files = [p[0] for p in sorted_paths]
    # print(sorted_path_to_py_files)
    return sorted_path_to_py_files


def get_root_url() -> str:
    args = sys.argv
    root_url = args[1]
    # print(root_url)
    return root_url


def check_file(url: str) -> list[StyleIssue]:
    checks_list: list[Check] = [
        CheckLineLength(),
        CheckIndentation(),
        CheckSemicolon(),
        CheckInlineComment(),
        CheckTodo(),
        CheckBlankLines(),
        CheckSpaceAfterConstruction(),
        CheckClassNames(),
        CheckFunctionNames(),
        CheckArgNames(),
        CheckDefaultValue(),
        CheckAssignNames()
    ]

    source_code = load_code_file(url)

    style_issues_list: list[StyleIssue] = []
    for ch in checks_list:
        style_issues = ch.do_check(source_code, url)
        style_issues_list = style_issues_list + style_issues

    sorted_style_issue_list = _sort_list(style_issues_list)
    return sorted_style_issue_list


# main #
def main():
    root_url = get_root_url()
    path_to_all_files = find_all_py_files(root_url)
    all_issues: list[StyleIssue] = []
    for f_url in path_to_all_files:
        # print(f_url)
        sil = check_file(f_url)
        all_issues = all_issues + sil

    pint_output(all_issues)


if __name__ == '__main__':
    main()

# def _check_line_length(line, code='S001', message='Too long'):
#     res_d = dict()
#     res_d['result'] = True
#     res_d['code'] = code
#     res_d['message'] = message
#     if len(line) <= 79 + 1:  # for \n char ???
#         pass
#     else:
#         res_d['result'] = False
#     return res_d
# def init_check_dict() -> dict:
#     check_d = dict()
#     check_d['line_length_check'] = _check_line_length
#
#     return check_d
# def check_file(url:str):
#     check_d = init_check_dict()
#
#     ln_list = load_code_file(url)
#
#     res_d_list = []
#     for i, line in enumerate(ln_list):
#         for check_name, check_funct in check_d.items():
#             res_d = check_funct(line)
#             if not res_d['result']:  # there is an issue
#                 res_d['line_nr'] = i + 1
#                 res_d_list.append(res_d)
#
#     pint_output(res_d_list)
