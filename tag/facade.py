from tag.models import Tag


def tag_get_path(tag: Tag):
    category = tag.category
    path = []
    while category is not None:
        path.append(category.name)
        category = category.parent_category
    return '/'.join(reversed(path))