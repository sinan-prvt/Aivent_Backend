def get_category_and_descendants(category):
    ids = [category.id]
    for child in category.children.all():
        ids.extend(get_category_and_descendants(child))
    return ids