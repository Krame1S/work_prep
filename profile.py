def prepare_profile(source: dict[str, object]) -> dict[str, object]:
    result = source.copy()
    tags_copy = source['tags'].copy()
    if result['status'] == 'draft':
        tags_copy.append('review')
    result['tags'] = tags_copy
    return result