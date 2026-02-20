from slugify import slugify

def generate_slug(text:str):
    return slugify(text)