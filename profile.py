def prepare_profile(source: dict[str, object]) -> dict[str, object]:
    result = source.copy()
    if result["status"] is "draft":
        result["tags"].append("review")
    return result