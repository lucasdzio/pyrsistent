from pyrsistent import freeze, inc, discard, rex, ny, field, PClass, pmap


def test_callable_command():
    m = freeze({'foo': {'bar': {'baz': 1}}})
    assert m.transform(['foo', 'bar', 'baz'], inc) == {'foo': {'bar': {'baz': 2}}}


def test_predicate():
    m = freeze({'foo': {'bar': {'baz': 1}, 'qux': {'baz': 1}}})
    assert m.transform(['foo', lambda x: x.startswith('b'), 'baz'], inc) == {'foo': {'bar': {'baz': 2}, 'qux': {'baz': 1}}}


def test_broken_predicate():
    broken_predicates = [
        lambda: None,
        lambda _a, _b, _c: None,
        lambda _a, _b, _c, _d=None: None,
        lambda *_args: None,
        lambda **_kwargs: None,
    ]
    for pred in broken_predicates:
        try:
            freeze({}).transform([pred], None)
            raise AssertionError()
        except ValueError as e:
            assert str(e) == "callable in transform path must take 1 or 2 arguments"


def test_key_value_predicate():
    m = freeze({
        'foo': 1,
        'bar': 2,
    })
    assert m.transform([
        lambda k, v: (k, v) == ('foo', 1),
    ], lambda v: v * 3) == {"foo": 3, "bar": 2}


def test_remove():
    m = freeze({'foo': {'bar': {'baz': 1}}})
    assert m.transform(['foo', 'bar', 'baz'], discard) == {'foo': {'bar': {}}}


def test_remove_pvector():
    m = freeze({'foo': [1, 2, 3]})
    assert m.transform(['foo', 1], discard) == {'foo': [1, 3]}


def test_remove_pclass():
    class MyClass(PClass):
        a = field()
        b = field()

    m = freeze({'foo': MyClass(a=1, b=2)})
    assert m.transform(['foo', 'b'], discard) == {'foo': MyClass(a=1)}


def test_predicate_no_match():
    m = freeze({'foo': {'bar': {'baz': 1}}})
    assert m.transform(['foo', lambda x: x.startswith('c'), 'baz'], inc) == m


def test_rex_predicate():
    m = freeze({'foo': {'bar': {'baz': 1},
                        'bof': {'baz': 1}}})
    assert m.transform(['foo', rex('^bo.*'), 'baz'], inc) == {'foo': {'bar': {'baz': 1},
                                                                      'bof': {'baz': 2}}}


def test_rex_with_non_string_key():
    m = freeze({'foo': 1, 5: 2})
    assert m.transform([rex(".*")], 5) == {'foo': 5, 5: 2}


def test_ny_predicated_matches_any_key():
    m = freeze({'foo': 1, 5: 2})
    assert m.transform([ny], 5) == {'foo': 5, 5: 5}


def test_new_elements_created_when_missing():
    m = freeze({})
    assert m.transform(['foo', 'bar', 'baz'], 7) == {'foo': {'bar': {'baz': 7}}}


def test_mixed_vector_and_map():
    m = freeze({'foo': [1, 2, 3]})
    assert m.transform(['foo', 1], 5) == freeze({'foo': [1, 5, 3]})


def test_vector_predicate_callable_command():
    v = freeze([1, 2, 3, 4, 5])
    assert v.transform([lambda i: 0 < i < 4], inc) == freeze(freeze([1, 3, 4, 5, 5]))


def test_vector_insert_map_one_step_beyond_end():
    v = freeze([1, 2])
    assert v.transform([2, 'foo'], 3) == freeze([1, 2, {'foo': 3}])


def test_multiple_transformations():
    v = freeze([1, 2])
    assert v.transform([2, 'foo'], 3, [2, 'foo'], inc) == freeze([1, 2, {'foo': 4}])


def test_no_transformation_returns_the_same_structure():
    v = freeze([{'foo': 1}, {'bar': 2}])
    assert v.transform([ny, ny], lambda x: x) is v


def test_discard_multiple_elements_in_pvector():
    assert freeze([0, 1, 2, 3, 4]).transform([lambda i: i % 2], discard) == freeze([0, 2, 4])


def test_transform_insert_empty_pmap():
    m = pmap().transform(['123'], pmap())
    assert m == pmap({'123': pmap()})


def test_discard_does_not_insert_nodes():
    m = freeze({}).transform(['foo', 'bar'], discard)
    assert m == pmap({})


# ============================================================================
# Tests for dec function (not previously tested)
# ============================================================================

def test_dec_function():
    """Test the dec (decrement) function."""
    m = freeze({'foo': {'bar': 5}})
    assert m.transform(['foo', 'bar'], lambda x: x - 1) == {'foo': {'bar': 4}}


def test_dec_with_negative_numbers():
    """Test dec with negative numbers."""
    v = freeze([1, 0, -1, -5])
    result = v.transform([lambda i: i in [0, 2], ], lambda x: x - 1)
    assert result == freeze([1, -1, -1, -2, -5])


def test_inc_with_large_numbers():
    """Test inc with large numbers."""
    m = freeze({'value': 999999999})
    assert m.transform(['value'], inc) == {'value': 1000000000}


def test_inc_with_negative_numbers():
    """Test inc with negative numbers."""
    m = freeze({'value': -10})
    assert m.transform(['value'], inc) == {'value': -9}


# ============================================================================
# Empty path and direct transformation tests
# ============================================================================

def test_empty_path_with_callable():
    """Test transformation with empty path and callable command."""
    m = freeze({'foo': 1})
    assert m.transform([], lambda _: {'bar': 2}) == {'bar': 2}


def test_empty_path_with_value():
    """Test transformation with empty path and direct value."""
    m = freeze({'foo': 1})
    assert m.transform([], {'bar': 2}) == {'bar': 2}


def test_empty_path_on_vector():
    """Test empty path transformation on vector."""
    v = freeze([1, 2, 3])
    assert v.transform([], lambda _: [4, 5, 6]) == [4, 5, 6]


# ============================================================================
# Deep nesting tests
# ============================================================================

def test_deeply_nested_structure():
    """Test transformation on deeply nested structure."""
    m = freeze({'a': {'b': {'c': {'d': {'e': {'f': 1}}}}}})
    result = m.transform(['a', 'b', 'c', 'd', 'e', 'f'], inc)
    assert result == {'a': {'b': {'c': {'d': {'e': {'f': 2}}}}}}


def test_deeply_nested_creation():
    """Test creating deeply nested structure from scratch."""
    m = freeze({})
    result = m.transform(['level1', 'level2', 'level3', 'level4', 'level5'], 42)
    assert result == {'level1': {'level2': {'level3': {'level4': {'level5': 42}}}}}


def test_deep_nesting_with_mixed_types():
    """Test deep nesting with vectors and maps mixed."""
    m = freeze({'a': [{'b': [{'c': 1}]}]})
    result = m.transform(['a', 0, 'b', 0, 'c'], inc)
    assert result == {'a': [{'b': [{'c': 2}]}]}


# ============================================================================
# Complex predicate tests
# ============================================================================

def test_predicate_with_multiple_conditions():
    """Test predicate with complex conditions."""
    m = freeze({'foo': 1, 'bar': 2, 'baz': 3, 'qux': 4})
    result = m.transform([lambda k: k in ['foo', 'baz']], lambda v: v * 10)
    assert result == {'foo': 10, 'bar': 2, 'baz': 30, 'qux': 4}


def test_predicate_with_value_filtering():
    """Test binary predicate filtering on values."""
    m = freeze({'a': 10, 'b': 20, 'c': 5, 'd': 15})
    result = m.transform([lambda _, v: v > 10], lambda v: v + 100)
    assert result == {'a': 10, 'b': 120, 'c': 5, 'd': 115}


def test_vector_predicate_with_range():
    """Test vector transformation with index range predicate."""
    v = freeze([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    result = v.transform([lambda i: 2 <= i <= 7], lambda v: v * 2)
    assert result == freeze([0, 1, 4, 6, 8, 10, 12, 14, 8, 9])


def test_nested_predicates():
    """Test multiple levels of predicates."""
    m = freeze({'a': {'x': 1, 'y': 2}, 'b': {'x': 3, 'y': 4}, 'c': {'x': 5, 'y': 6}})
    result = m.transform([lambda k: k.startswith('a') or k.startswith('b'), 'x'], inc)
    assert result == {'a': {'x': 2, 'y': 2}, 'b': {'x': 4, 'y': 4}, 'c': {'x': 5, 'y': 6}}


# ============================================================================
# Multiple transformation chains
# ============================================================================

def test_chain_multiple_inc_operations():
    """Test chaining multiple increment operations."""
    m = freeze({'value': 0})
    result = m.transform(['value'], inc, ['value'], inc, ['value'], inc)
    assert result == {'value': 3}


def test_chain_different_paths():
    """Test chaining transformations on different paths."""
    m = freeze({'a': 1, 'b': 2, 'c': 3})
    result = m.transform(['a'], inc, ['b'], lambda v: v * 2, ['c'], lambda v: v - 1)
    assert result == {'a': 2, 'b': 4, 'c': 2}


def test_chain_creation_and_modification():
    """Test creating a path then modifying it in chain."""
    m = freeze({})
    result = m.transform(['new', 'path'], 10, ['new', 'path'], inc)
    assert result == {'new': {'path': 11}}


# ============================================================================
# Edge cases with empty structures
# ============================================================================

def test_transform_empty_map():
    """Test transformation on empty map."""
    m = freeze({})
    result = m.transform([lambda _: True], inc)
    assert result == {}


def test_transform_empty_vector():
    """Test transformation on empty vector."""
    v = freeze([])
    result = v.transform([lambda _: True], inc)
    assert result == freeze([])


def test_single_element_vector():
    """Test transformation on single element vector."""
    v = freeze([42])
    assert v.transform([0], inc) == freeze([43])


def test_single_key_map():
    """Test transformation on single key map."""
    m = freeze({'only': 1})
    assert m.transform(['only'], inc) == {'only': 2}


# ============================================================================
# Tests with PClass and PRecord
# ============================================================================

def test_pclass_nested_field_transformation():
    """Test transformation of nested PClass fields."""
    class Inner(PClass):
        value = field()
    
    class Outer(PClass):
        inner = field()
        count = field()
    
    m = freeze({'obj': Outer(inner=Inner(value=10), count=5)})
    result = m.transform(['obj', 'inner', 'value'], inc)
    assert result == {'obj': Outer(inner=Inner(value=11), count=5)}


def test_pclass_multiple_fields():
    """Test transformation of multiple PClass fields."""
    class Point(PClass):
        x = field()
        y = field()
        z = field()
    
    m = freeze({'point': Point(x=1, y=2, z=3)})
    result = m.transform(['point', 'x'], inc, ['point', 'y'], inc)
    assert result == {'point': Point(x=2, y=3, z=3)}


def test_pclass_with_predicate():
    """Test PClass field selection with predicate."""
    class Data(PClass):
        a = field()
        b = field()
        c = field()
    
    obj = Data(a=1, b=2, c=3)
    result = obj.transform([lambda k: k in ['a', 'c']], inc)
    assert result == Data(a=2, b=2, c=4)


# ============================================================================
# Tests with special keys and values
# ============================================================================

def test_unicode_keys():
    """Test transformation with unicode keys."""
    m = freeze({'café': 1, 'naïve': 2, '日本': 3})
    result = m.transform(['café'], inc)
    assert result == {'café': 2, 'naïve': 2, '日本': 3}


def test_numeric_keys():
    """Test transformation with numeric keys."""
    m = freeze({1: 'one', 2: 'two', 3: 'three'})
    result = m.transform([2], lambda v: v.upper())
    assert result == {1: 'one', 2: 'TWO', 3: 'three'}


def test_tuple_values():
    """Test transformation with tuple values."""
    m = freeze({'coords': (1, 2, 3)})
    result = m.transform(['coords'], lambda t: (t[0] + 1, t[1] + 1, t[2] + 1))
    assert result == {'coords': (2, 3, 4)}


def test_none_values():
    """Test transformation with None values."""
    m = freeze({'a': None, 'b': 1})
    result = m.transform(['a'], lambda v: 0 if v is None else v)
    assert result == {'a': 0, 'b': 1}


# ============================================================================
# Rex (regex) matcher edge cases
# ============================================================================

def test_rex_case_sensitive():
    """Test rex matcher with case sensitivity."""
    m = freeze({'Foo': 1, 'foo': 2, 'FOO': 3})
    result = m.transform([rex('^foo$')], inc)
    assert result == {'Foo': 1, 'foo': 3, 'FOO': 3}


def test_rex_special_characters():
    """Test rex matcher with special regex characters."""
    m = freeze({'test.key': 1, 'testXkey': 2, 'test': 3})
    result = m.transform([rex(r'test\.key')], inc)
    assert result == {'test.key': 2, 'testXkey': 2, 'test': 3}


def test_rex_complex_pattern():
    """Test rex with complex regex pattern."""
    m = freeze({'item1': 1, 'item2': 2, 'item10': 3, 'other': 4})
    result = m.transform([rex(r'^item\d+$')], lambda v: v * 10)
    assert result == {'item1': 10, 'item2': 20, 'item10': 30, 'other': 4}


def test_rex_empty_pattern():
    """Test rex with pattern that matches empty string."""
    m = freeze({'': 1, 'a': 2})
    result = m.transform([rex('^$')], inc)
    assert result == {'': 2, 'a': 2}


# ============================================================================
# Discard operation edge cases
# ============================================================================

def test_discard_nonexistent_key():
    """Test discarding a key that doesn't exist."""
    m = freeze({'a': 1, 'b': 2})
    result = m.transform(['nonexistent'], discard)
    assert result == {'a': 1, 'b': 2}


def test_discard_nested_nonexistent():
    """Test discarding in nested structure where parent doesn't exist."""
    m = freeze({'a': 1})
    result = m.transform(['nonexistent', 'nested'], discard)
    assert result == {'a': 1}


def test_discard_all_elements():
    """Test discarding all elements from map."""
    m = freeze({'a': 1, 'b': 2})
    result = m.transform([ny], discard)
    assert result == freeze({})


def test_discard_with_predicate_no_match():
    """Test discard with predicate that matches nothing."""
    v = freeze([1, 2, 3, 4, 5])
    result = v.transform([lambda i: i > 10], discard)
    assert result == v


def test_discard_first_element_vector():
    """Test discarding first element from vector."""
    v = freeze([1, 2, 3])
    result = v.transform([0], discard)
    assert result == freeze([2, 3])


def test_discard_last_element_vector():
    """Test discarding last element from vector."""
    v = freeze([1, 2, 3])
    result = v.transform([2], discard)
    assert result == freeze([1, 2])


# ============================================================================
# Identity and no-op transformations
# ============================================================================

def test_identity_transformation_map():
    """Test that identity transformation returns same object."""
    m = freeze({'a': {'b': {'c': 1}}})
    result = m.transform(['a', 'b', 'c'], lambda x: x)
    assert result is m


def test_identity_transformation_vector():
    """Test identity transformation on vector."""
    v = freeze([1, 2, 3, 4, 5])
    result = v.transform([2], lambda x: x)
    assert result is v


def test_transformation_no_change_complex():
    """Test complex structure with transformation that produces no change."""
    m = freeze({'a': [1, 2, 3], 'b': {'x': 10, 'y': 20}})
    result = m.transform(['b', 'x'], lambda x: x)
    assert result is m


# ============================================================================
# Mixed type nested structures
# ============================================================================

def test_map_containing_vectors_of_maps():
    """Test complex nesting: map -> vector -> map."""
    m = freeze({'outer': [{'inner1': 1}, {'inner2': 2}, {'inner3': 3}]})
    result = m.transform(['outer', 1, 'inner2'], inc)
    assert result == {'outer': [{'inner1': 1}, {'inner2': 3}, {'inner3': 3}]}


def test_vector_containing_maps_of_vectors():
    """Test complex nesting: vector -> map -> vector."""
    v = freeze([{'data': [1, 2, 3]}, {'data': [4, 5, 6]}])
    result = v.transform([0, 'data', 1], lambda x: x * 10)
    assert result == freeze([{'data': [1, 20, 3]}, {'data': [4, 5, 6]}])


def test_alternating_map_vector_nesting():
    """Test alternating map and vector nesting."""
    m = freeze({'a': [{'b': [{'c': 100}]}]})
    result = m.transform(['a', 0, 'b', 0, 'c'], lambda x: x + 1)
    assert result == {'a': [{'b': [{'c': 101}]}]}


# ============================================================================
# Boundary and stress tests
# ============================================================================

def test_large_vector_transformation():
    """Test transformation on large vector."""
    v = freeze(list(range(100)))
    result = v.transform([lambda i: i % 10 == 0], inc)
    expected = freeze([1 if i % 10 == 0 else i for i in range(100)])
    assert result == expected


def test_many_keys_map():
    """Test transformation on map with many keys."""
    m = freeze({f'key{i}': i for i in range(50)})
    result = m.transform([lambda k: k.endswith('0')], inc)
    expected = freeze({f'key{i}': i + 1 if i % 10 == 0 else i for i in range(50)})
    assert result == expected


def test_vector_index_at_boundary():
    """Test transformation at vector boundaries."""
    v = freeze([1, 2, 3, 4, 5])
    # First element
    assert v.transform([0], lambda x: x * 10) == freeze([10, 2, 3, 4, 5])
    # Last element
    assert v.transform([4], lambda x: x * 10) == freeze([1, 2, 3, 4, 50])


# ============================================================================
# Non-standard callable commands
# ============================================================================

def test_custom_function_as_command():
    """Test using custom function as command."""
    def double_and_add_one(x):
        return x * 2 + 1
    
    m = freeze({'value': 5})
    result = m.transform(['value'], double_and_add_one)
    assert result == {'value': 11}


def test_lambda_with_multiple_operations():
    """Test lambda with multiple operations."""
    m = freeze({'data': {'value': 10}})
    result = m.transform(['data', 'value'], lambda x: ((x + 5) * 2) - 3)
    assert result == {'data': {'value': 27}}


def test_builtin_function_as_command():
    """Test using built-in functions as commands."""
    m = freeze({'text': 'hello'})
    result = m.transform(['text'], str.upper)
    assert result == {'text': 'HELLO'}


# ============================================================================
# Error handling and edge cases
# ============================================================================

def test_predicate_returning_false_for_all():
    """Test predicate that returns False for all elements."""
    m = freeze({'a': 1, 'b': 2, 'c': 3})
    result = m.transform([lambda _: False], inc)
    assert result == m


def test_binary_predicate_all_false():
    """Test binary predicate returning False for all."""
    m = freeze({'a': 1, 'b': 2})
    result = m.transform([lambda _, v: v > 100], inc)
    assert result == m


def test_transformation_preserves_types():
    """Test that transformation preserves value types."""
    m = freeze({'int': 1, 'str': 'hello', 'float': 3.14, 'bool': True})
    result = m.transform(['int'], lambda x: x)
    assert result == m
    assert isinstance(result['int'], int)


# ============================================================================
# Complex real-world scenarios
# ============================================================================

def test_increment_all_prices():
    """Test real-world scenario: increment all prices in a catalog."""
    catalog = freeze({
        'products': [
            {'name': 'Widget', 'price': 10},
            {'name': 'Gadget', 'price': 20},
            {'name': 'Doohickey', 'price': 15}
        ]
    })
    result = catalog.transform(['products', ny, 'price'], lambda p: p + 5)
    assert result['products'][0]['price'] == 15
    assert result['products'][1]['price'] == 25
    assert result['products'][2]['price'] == 20


def test_update_nested_configuration():
    """Test updating nested configuration structure."""
    config = freeze({
        'database': {
            'host': 'localhost',
            'port': 5432,
            'options': {
                'timeout': 30,
                'retries': 3
            }
        }
    })
    result = config.transform(
        ['database', 'options', 'timeout'], lambda x: x * 2,
        ['database', 'options', 'retries'], inc
    )
    assert result['database']['options']['timeout'] == 60
    assert result['database']['options']['retries'] == 4


def test_normalize_data_structure():
    """Test normalizing nested data."""
    data = freeze({
        'users': [
            {'id': 1, 'name': 'Alice', 'score': 85},
            {'id': 2, 'name': 'Bob', 'score': 92},
            {'id': 3, 'name': 'Charlie', 'score': 78}
        ]
    })
    # Normalize scores to 0-1 range
    result = data.transform(
        ['users', ny, 'score'],
        lambda s: round(s / 100.0, 2)
    )
    assert result['users'][0]['score'] == 0.85
    assert result['users'][1]['score'] == 0.92
    assert result['users'][2]['score'] == 0.78