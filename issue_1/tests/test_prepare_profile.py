import pytest
from prepare_profile import prepare_profile
from copy import deepcopy


def test_draft_by_value():
    source = {'status': ''.join(['dr', 'aft']), 'tags': ['tag1'], 'name': 'Name'}
    result = prepare_profile(source)
    assert result == {'status': ''.join(['dr', 'aft']), 'tags': ['tag1', 'review'], 'name': 'Name'}


def test_published_no_review():
    source = {'status': 'published', 'tags': ['tag1'], 'name': 'Name'}
    result = prepare_profile(source)
    assert result == {'status': 'published', 'tags': ['tag1'], 'name': 'Name'}


def test_source_and_tags_unchanged():
    source = {'status': 'draft', 'tags': ['tag1']}
    source_copy = deepcopy(source)
    result = prepare_profile(source)
    assert source == source_copy     # он покрывает оба условия но для явности 2 assert
    assert source['tags'] == source_copy['tags']

    
def test_result_is_new_dict():
    source = {'status': 'draft', 'tags': ['tag1']}
    result = prepare_profile(source)
    assert result is not source


@pytest.mark.parametrize("status", ["draft", "published"])
def test_tags_is_new_list(status):
    source = {'status': status, 'tags': ['tag1']}
    result = prepare_profile(source)
    assert result['tags'] is not source['tags']


@pytest.mark.parametrize("status", ["draft", "published"])
def test_changing_result_does_not_affect_source(status):
    source = {'status': status, 'tags': ['tag1']}
    result = prepare_profile(source)
    result['tags'].append('not_in_source')
    assert 'not_in_source' not in source['tags']