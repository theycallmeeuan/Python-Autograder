from __future__ import annotations

import ast
import os
import sys
import re
from typing import NamedTuple, Sequence,Any, List, Dict, Set
from grading.best_practises import built_in_func_def
from types import FunctionType

class Violation(NamedTuple):
    """
    Every rule violation contains a node that breaks the rule,
    and a message that will be shown to the user.
    """

    node: ast.AST
    message: str

class Checker(ast.NodeVisitor):
    """
    A Checker is a Visitor that defines a lint rule, and stores all the
    nodes that violate that lint rule.
    """

    def __init__(self, issue_code: str) -> None:
        self.issue_code = issue_code
        self.violations: set[Violation] = set()

class Linter:
    """Holds all list rules, and runs them against a source file."""

    def __init__(self):
        self.checkers: set[Checker] = set()

    @staticmethod
    def print_violations(checker: Checker, file_name: str) -> None:
        """Prints all violations collected by a checker."""
        for node, message in checker.violations:
            print(
                f"{file_name}:{node.lineno}:{node.col_offset}: "
                f"{checker.issue_code}: {message}"
            )

    @staticmethod
    def store_volations(checker: Checker) :
        """Store all violations collected by a checker."""
        violatons_dict = {}
        for node, message in checker.violations:
            violation_details = {"line":node.lineno,"message":message}
            if(checker.issue_code in violatons_dict):
                violatons_dict[checker.issue_code].append(violation_details)
            else:
                violatons_dict[checker.issue_code] = [violation_details]
        return violatons_dict

    def run(self, source_code: str):
        """Runs all lints on a source file."""
        all_violations = {}
        file_name = 'file'

        tree = ast.parse(source_code)
        for checker in self.checkers:
            checker.visit(tree)
            violations = self.store_volations(checker)
            if (len(violations) != 0):
                all_violations.update(violations)
            #self.print_violations(checker, file_name)
        return {file_name:all_violations}

class UnusedVariableInScopeChecker(Checker):
    """Checks if any variables are unused in this node's scope."""

    def __init__(self, issue_code: str) -> None:
        super().__init__(issue_code)
        # unused_names is a dictionary that stores variable names, and
        # whether or not they've been found in a "Load" context yet.
        # If it's found to be used, its value is turned to False.
        self.unused_names: dict[str, bool] = {}

        # name_nodes holds the first occurences of variables.
        self.name_nodes: dict[str, ast.Name] = {}

    def visit_Name(self, node: ast.Name) -> None:
        """Find all nodes that only exist in `Store` context"""
        var_name = node.id

        if isinstance(node.ctx, ast.Store):
            # If it's a new name, save the node for later
            if var_name not in self.name_nodes:
                self.name_nodes[var_name] = node

            # If we've never seen it before, it is unused.
            if var_name not in self.unused_names:
                self.unused_names[var_name] = True

        else:
            # It's used somewhere.
            self.unused_names[var_name] = False

class UnusedVariableChecker(Checker):
    def check_for_unused_variables(self, node: ast.AST) -> None:
        """Find unused variables in the local scope of this node."""
        visitor = UnusedVariableInScopeChecker(self.issue_code)
        visitor.visit(node)

        for name, unused in visitor.unused_names.items():
            if unused:
                node = visitor.name_nodes[name]
                self.violations.add(Violation(node, f"Unused variable: {name}"))

    def visit_Module(self, node: ast.Module) -> None:
        self.check_for_unused_variables(node)
        super().generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.check_for_unused_variables(node)
        super().generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.check_for_unused_variables(node)
        super().generic_visit(node)

class VariableNamingConventionChecker(Checker):
    """Checks if variables follow the snake_case naming convention."""
    def __init__(self, issue_code: str) -> None:
        super().__init__(issue_code)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            if not re.match(r'^[a-z_][a-z0-9_]*$', node.id):
                self.violations.add(Violation(node, f"Variable '{node.id}' does not follow snake_case naming convention"))
    
class InfiniteLoopChecker(Checker):
    """Checks for potential infinite loops."""

    def visit_While(self, node: ast.While) -> None:
        self._check_infinite_loop(node)
        super().generic_visit(node)
        

    def visit_For(self, node: ast.For) -> None:
        self._check_infinite_for_loop(node)
        super().generic_visit(node)

    def _check_infinite_loop(self, node: ast.While) -> None:
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            if not any(isinstance(stmt, (ast.Break, ast.Return, ast.Raise)) for stmt in ast.walk(node)):
                self.violations.add(Violation(node, "Potential infinite loop: while True without break, return, or raise"))
        
        # Check for loops that don't modify their condition
        condition_vars = self._get_condition_variables(node.test)
        if not self._variables_modified_in_loop(condition_vars, node.body):
            self.violations.add(Violation(node, "Potential infinite loop: loop condition variables are not modified inside the loop"))

    def _check_infinite_for_loop(self, node: ast.For) -> None:
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == 'range' and len(node.iter.args) == 1:
                # Check for 'for i in range(1):' pattern
                if isinstance(node.iter.args[0], ast.Constant) and node.iter.args[0].value == 1:
                    self.violations.add(Violation(node, "Potential infinite loop: for loop with range(1)"))

    def _get_condition_variables(self, condition: ast.AST) -> set[str]:
        variables = set()
        for node in ast.walk(condition):
            if isinstance(node, ast.Name):
                variables.add(node.id)
        return variables

    def _variables_modified_in_loop(self, variables: set[str], body: list[ast.AST]) -> bool:
        for node in ast.walk(ast.Module(body=body)):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in variables:
                        return True
            elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
                if node.target.id in variables:
                    return True
        return False
    
class IncorrectDataTypeChecker(Checker):
    """Checks for potential incorrect data types or improper type conversions."""

    def __init__(self, issue_code: str) -> None:
        super().__init__(issue_code)
        self.type_context: Dict[str, Set[str]] = {}
        self.in_built_variables = built_in_func_def.get_final_in_built_variables()


    def visit_Assign(self, node: ast.Assign) -> None:
        self._check_assignment(node)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._check_augmented_assignment(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        self._check_type_conversion(node)
        self.generic_visit(node)

    def _check_assignment(self, node: ast.Assign) -> None:
        value_type = self._infer_type(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                #print(node.value,target.id,value_type)
                self._update_type_context(target.id, value_type)
                self._check_type_mismatch(target.id, value_type)

    def _check_augmented_assignment(self, node: ast.AugAssign) -> None:
        if isinstance(node.target, ast.Name):
            value_type = self._infer_type(node.value)
            target_type = self._get_type_from_context(node.target.id)
            if target_type and value_type and target_type != value_type:
                #print(node.value.left.value)
                self.violations.add(Violation(node, f"Potential type mismatch in augmented assignment: {target_type,node.target.id} wants to {node.op.__class__.__name__.lower()} with {value_type,node.target.id}"))

    def _check_type_conversion(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in ['int', 'float', 'str', 'bool']:
            if len(node.args) == 1:
                arg_type = self._infer_type(node.args[0])
                if arg_type and arg_type == node.func.id:
                    self.violations.add(Violation(node, f"Unnecessary type conversion: {arg_type} to {node.func.id}"))

    def _infer_type(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.Name):
            print(node.id)
            return self._get_type_from_context(node.id)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                var_type = self.in_built_variables.get(node.func.id, FunctionType)
                return var_type[0] if isinstance(var_type,list) else var_type ### gotta fix this sum:[int,float] but idk how to determine binOP result
        return "unknown"

    def _update_type_context(self, name: str, type_: str) -> None:
        if name not in self.type_context:
            self.type_context[name] = set()
        self.type_context[name].add(type_)

    def _get_type_from_context(self, name: str) -> str:
        if name in self.type_context:
            types = self.type_context[name]
            return list(types)[0] if len(types) == 1 else "mixed"
        return "unknown"

    def _check_type_mismatch(self, name: str, new_type: str) -> None:
        if name in self.type_context:
            existing_types = self.type_context[name]
            if new_type not in existing_types and "unknown" not in existing_types:
                self.violations.add(Violation(ast.Name(id=name), f"Potential type mismatch: variable '{name}' previously had type(s) {', '.join(existing_types)}, now assigned {new_type}"))

class RedundantCodeChecker(Checker):
    """Checks for redundant code patterns."""

    def visit_Assign(self, node: ast.Assign) -> None:
        self._check_redundant_assignment(node)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self._check_redundant_if_else(node)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        self._check_redundant_comparison(node)
        self.generic_visit(node)

    def _check_redundant_assignment(self, node: ast.Assign) -> None:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Name):
            if node.targets[0].id == node.value.id:
                self.violations.add(Violation(node, f"Redundant assignment: {node.targets[0].id} = {node.value.id}"))

    def _check_redundant_if_else(self, node: ast.If) -> None:
        if isinstance(node.test, ast.Constant):
            if node.test.value:
                self.violations.add(Violation(node, "Always true if condition"))
            else:
                self.violations.add(Violation(node, "Always false if condition"))
        
        if node.orelse and len(node.body) == 1 and len(node.orelse) == 1:
            if (isinstance(node.body[0], ast.Return) and isinstance(node.orelse[0], ast.Return) and
                isinstance(node.body[0].value, ast.Constant) and isinstance(node.orelse[0].value, ast.Constant)):
                if node.body[0].value.value is True and node.orelse[0].value.value is False:
                    self.violations.add(Violation(node, f"Redundant if-else, can be simplified to: return {ast.unparse(node.test)}"))

    def _check_redundant_comparison(self, node: ast.Compare) -> None:
        if len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
            if (isinstance(node.left, ast.Constant) and isinstance(node.comparators[0], ast.Constant) and
                type(node.left.value) == type(node.comparators[0].value)):
                result = node.left.value == node.comparators[0].value
                if isinstance(node.ops[0], ast.NotEq):
                    result = not result
                self.violations.add(Violation(node, f"Redundant comparison, always evaluates to {result}"))

        if len(node.ops) == 1 and isinstance(node.ops[0], (ast.In, ast.NotIn)):
            if isinstance(node.comparators[0], (ast.List, ast.Tuple, ast.Set)) and len(node.comparators[0].elts) == 0:
                result = False if isinstance(node.ops[0], ast.In) else True
                self.violations.add(Violation(node, f"Redundant membership test with empty container, always evaluates to {result}"))


def best_practice_checker(student_code) -> dict:
    all_violations = {}
    #print(student_path)
    linter = Linter()
    # linter.checkers.add(SetDuplicateItemChecker(issue_code="W001"))
    linter.checkers.add(UnusedVariableChecker(issue_code="VARMGT001"))
    linter.checkers.add(VariableNamingConventionChecker(issue_code="VARMGT002"))
    linter.checkers.add(InfiniteLoopChecker(issue_code="LOGIC003"))
    linter.checkers.add(IncorrectDataTypeChecker(issue_code="DATA001"))
    linter.checkers.add(RedundantCodeChecker(issue_code="PERF002"))



    violations = linter.run(student_code)
    all_violations.update(violations)
    return all_violations
##########################################################################################################################
##########################################################################################################################
# v = best_practice_checker("C:\\Users\\ashup\\Desktop\\Y5S1\\FYP\\python_openAI\\student.py")
# print(v)