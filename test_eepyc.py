import unittest

from eepyc import Evaluator


class TestEepyc(unittest.TestCase):
    def test_expression(self):
        e = Evaluator()
        self.assertEqual(e.eval_tags("{{ 1 + 2 }}"), "3")

    def test_expression_list(self):
        e = Evaluator()
        self.assertEqual(e.eval_tags("{{ ['apple', 'banana'] }}"), "apple\nbanana")

    def test_statement(self):
        e = Evaluator()
        self.assertEqual(e.eval_tags("{{% x = 7 }}{{ x }}"), "7")

    def test_statement_print(self):
        e = Evaluator()
        self.assertEqual(e.eval_tags("{{% print('hello') }}"), "hello")

    def test_newline_strip(self):
        e = Evaluator()
        self.assertEqual(e.eval_tags("\n\n\t{{- 9 -}}\n\n"), "\n\t9\n")

    def test_newline_strip_too_many(self):
        e = Evaluator()
        self.assertEqual(e.eval_tags("\n\n\t{{--- 9 ---}}\n\n"), "\t9")

    def test_indented_list(self):
        e = Evaluator()
        self.assertEqual(e.eval_tags("\n\t{{ [1, 2] }}"), "\n\t1\n\t2")

    def test_indent_without_preceding_newline(self):
        e = Evaluator()
        self.assertEqual(e.eval_tags("\t{{ [1, 2] }}"), "\t1\n\t2")

    def test_no_indent(self):
        e = Evaluator()
        self.assertEqual(e.eval_tags("\n\t{{-^ 6 }}"), "6")
