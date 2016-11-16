# -*- coding: utf-8 -*-
import pytest

from patternmatcher.constraints import CustomConstraint, MultiConstraint
from patternmatcher.expressions import Operation, Symbol, Variable, Arity, Wildcard, freeze
from patternmatcher.matching import CommutativePatternsParts

f = Operation.new('f', Arity.variadic)
f2 = Operation.new('f2', Arity.variadic)
fc = Operation.new('fc', Arity.variadic, commutative=True)
fc2 = Operation.new('fc2', Arity.variadic, commutative=True)
fa = Operation.new('fa', Arity.variadic, associative=True)
fa2 = Operation.new('fa2', Arity.variadic, associative=True)
fac1 = Operation.new('fac1', Arity.variadic, associative=True, commutative=True)
fac2 = Operation.new('fac2', Arity.variadic, associative=True, commutative=True)
a = Symbol('a')
b = Symbol('b')
c = Symbol('c')
_ = Wildcard.dot()
x_ = Variable.dot('x')
x2 = Variable.fixed('x', 2)
y_ = Variable.dot('y')
z_ = Variable.dot('z')
__ = Wildcard.plus()
x__ = Variable.plus('x')
y__ = Variable.plus('y')
z__ = Variable.plus('z')
___ = Wildcard.star()
x___ = Variable.star('x')
y___ = Variable.star('y')
z___ = Variable.star('z')

constr1 = CustomConstraint(lambda x, y: x == y)
constr2 = CustomConstraint(lambda x, y: x != y)


class TestCommutativePatternsParts:
    @pytest.mark.parametrize(
        '   expressions,                    constant,       syntactic,      sequence_variables,     fixed_variables,        rest',
        [
            ([],                            [],             [],             [],                     [],                     []),
            ([a],                           [a],            [],             [],                     [],                     []),
            ([a, b],                        [a, b],         [],             [],                     [],                     []),
            ([x_],                          [],             [],             [],                     [('x', 1)],             []),
            ([x_, y_],                      [],             [],             [],                     [('x', 1), ('y', 1)],   []),
            ([x2],                          [],             [],             [],                     [('x', 2)],             []),
            ([f(x_)],                       [],             [f(x_)],        [],                     [],                     []),
            ([f(x_), f(y_)],                [],             [f(x_), f(y_)], [],                     [],                     []),
            ([f(a)],                        [f(a)],         [],             [],                     [],                     []),
            ([f(x__)],                      [],             [],             [],                     [],                     [f(x__)]),
            ([f(a), f(b)],                  [f(a), f(b)],   [],             [],                     [],                     []),
            ([x__],                         [],             [],             [('x', 1)],             [],                     []),
            ([x___],                        [],             [],             [('x', 0)],             [],                     []),
            ([x__, y___],                   [],             [],             [('x', 1), ('y', 0)],   [],                     []),
            ([fc(x_)],                      [],             [],             [],                     [],                     [fc(x_)]),
            ([fc(x_, a)],                   [],             [],             [],                     [],                     [fc(x_, a)]),
            ([fc(x_, a), fc(x_, b)],        [],             [],             [],                     [],                     [fc(x_, a), fc(x_, b)]),
            ([fc(a)],                       [fc(a)],        [],             [],                     [],                     []),
            ([fc(a), fc(b)],                [fc(a), fc(b)], [],             [],                     [],                     []),
            ([a, x_, x__, f(x_), fc(x_)],   [a],            [f(x_)],        [('x', 1)],             [('x', 1)],             [fc(x_)]),
            ([__],                          [],             [],             [(None, 1)],            [],                     []),
            ([_],                           [],             [],             [],                     [(None, 1)],            []),
        ]
    )
    def test_parts(self, expressions, constant, syntactic, sequence_variables, fixed_variables, rest):
        parts = CommutativePatternsParts(None, *map(freeze, expressions))

        assert constant == sorted(parts.constant)
        assert syntactic == sorted(parts.syntactic)

        assert len(sequence_variables) == len(parts.sequence_variables)
        for name, min_count in sequence_variables:
            assert name in parts.sequence_variables
            assert name in parts.sequence_variable_infos
            assert min_count == parts.sequence_variable_infos[name].min_count

        assert len(fixed_variables) == len(parts.fixed_variables)
        for name, min_count in fixed_variables:
            assert name in parts.fixed_variables
            assert name in parts.fixed_variable_infos
            assert min_count == parts.fixed_variable_infos[name].min_count

        assert rest == sorted(parts.rest)

        assert sum(c for _, c in sequence_variables) == parts.sequence_variable_min_length
        assert sum(c for _, c in fixed_variables) == parts.fixed_variable_length

    @pytest.mark.parametrize(
        '   constraints,                        result_constraint',
        [
            ([None],                            None),
            ([constr1],                         constr1),
            ([constr1,  constr1],               constr1),
            ([None,     constr1],               constr1),
            ([constr1,  None],                  constr1),
            ([None,     None,       constr1],   constr1),
            ([None,     constr1,    None],      constr1),
            ([constr1,  None,       None],      constr1),
            ([constr1,  constr2],               MultiConstraint(constr1, constr2)),
            ([None,     constr1,    constr2],   MultiConstraint(constr1, constr2)),
            ([constr1,  None,       constr2],   MultiConstraint(constr1, constr2)),
            ([constr1,  constr2,    None],      MultiConstraint(constr1, constr2))
        ]
    )
    def test_fixed_var_constraints(self, constraints, result_constraint):
        parts = CommutativePatternsParts(None, *[Variable('x', Wildcard.dot(), c) for c in constraints])

        assert 1 == len(parts.fixed_variables.keys())
        assert len(constraints) == len(parts.fixed_variables)
        assert 'x' in parts.fixed_variables
        assert 'x' in parts.fixed_variable_infos

        info = parts.fixed_variable_infos['x']
        assert 1 == info.min_count
        assert result_constraint == info.constraint

    @pytest.mark.parametrize(
        '   constraints,                        result_constraint',
        [
            ([None],                            None),
            ([constr1],                         constr1),
            ([constr1,  constr1],               constr1),
            ([None,     constr1],               constr1),
            ([constr1,  None],                  constr1),
            ([None,     None,       constr1],   constr1),
            ([None,     constr1,    None],      constr1),
            ([constr1,  None,       None],      constr1),
            ([constr1,  constr2],               MultiConstraint(constr1, constr2)),
            ([None,     constr1,    constr2],   MultiConstraint(constr1, constr2)),
            ([constr1,  None,       constr2],   MultiConstraint(constr1, constr2)),
            ([constr1,  constr2,    None],      MultiConstraint(constr1, constr2))
        ]
    )
    def test_sequence_var_constraints(self, constraints, result_constraint):
        parts = CommutativePatternsParts(None, *[Variable('x', Wildcard.plus(), c) for c in constraints])

        assert 1 == len(parts.sequence_variables.keys())
        assert len(constraints) == len(parts.sequence_variables)
        assert 'x' in parts.sequence_variables
        assert 'x' in parts.sequence_variable_infos

        info = parts.sequence_variable_infos['x']
        assert 1 == info.min_count
        assert result_constraint == info.constraint


if __name__ == '__main__':
    import patternmatcher.matching as tested_module
    pytest.main(['--doctest-modules', __file__, tested_module.__file__])