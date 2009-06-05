try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from PIL import Image


def is_valid_image(supposed_image):
    """Verifies that the file (like) object is a valid image"""
    # We need to get a file object for PIL. We might have a path or we might
    # have to read the data into memory.
    if hasattr(supposed_image, 'temporary_file_path'):
        file = supposed_image.temporary_file_path()
    else:
        if hasattr(supposed_image, 'read'):
            file = StringIO(supposed_image.read())
        else:
            file = StringIO(supposed_image['content'])

    try:
        # load() is the only method that can spot a truncated JPEG,
        #  but it cannot be called sanely after verify()
        trial_image = Image.open(file)
        trial_image.load()

        # Since we're about to use the file again we have to reset the
        # file object if possible.
        if hasattr(file, 'reset'):
            file.reset()

        # verify() is the only method that can spot a corrupt PNG,
        #  but it must be called immediately after the constructor
        trial_image = Image.open(file)
        trial_image.verify()
    except Exception: # Python Imaging Library doesn't recognize it as an image
        return False
    if hasattr(supposed_image, 'seek') and callable(supposed_image.seek):
        supposed_image.seek(0)
    
    return True
