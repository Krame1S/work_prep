from work_prep.profile import prepare_profile
from copy import deepcopy


def test_draft_by_value():
    source = {'status': ''.join(['dr', 'aft']), 'tags': ['tag1']}
    result = prepare_profile(source)
    assert 'review' in result['tags']


def test_source_and_tags_unchanged():
    source = {'status': 'draft', 'tags': ['tag1']}
    source_copy = deepcopy(source)
    result = prepare_profile(source)
    assert source == source_copy     #он покрывает оба условия но для явности 2 assert
    assert source['tags'] == source_copy['tags']


def test_result_is_new_dict():
    source = {'status': 'draft', 'tags': ['tag1']}
    result = prepare_profile(source)
    assert result is not source


def test_tags_is_new_list():
    source = {'status': 'draft', 'tags': ['tag1']}
    result = prepare_profile(source)
    assert result['tags'] is not source['tags']


def test_no_draft_no_review():
    source = {'status': 'not_draft', 'tags': ['tag1']}
    result = prepare_profile(source)
    assert 'review' not in result['tags']


def test_changing_result_does_not_affect_source():
    source = {'status': 'draft', 'tags': ['tag1']}
    result = prepare_profile(source)
    result['tags'].append('not_in_source')
    assert 'not_in_source' not in source['tags']