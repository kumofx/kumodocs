import hashlib
import os

import KIOutils


def check_img(fn, content, hashes):
    assert hashlib.md5(content).hexdigest() in hashes, '{} does not match samples'.format(fn)


def check_doc(fn, content):
    fp = os.path.abspath(os.path.join(KIOutils.dir_path(__file__), 'samples', 'docstest', fn))
    with open(fp, 'rb') as f:
        sample_content = f.read()
    assert sample_content == content, '{} != {}'.format(sample_content, content)


def hash_sample_images(objects):
    sample_images = read_sample_images('docstest')
    return {hashlib.md5(img).hexdigest() for img in sample_images}


def is_image(filename):
    return not (filename.endswith('.pdf') or filename.endswith('.txt'))


def read_sample_images(sample):
    base_dir = os.path.abspath(os.path.join(KIOutils.dir_path(__file__), 'samples', sample))
    files = (f for f in os.listdir(base_dir) if is_image(f))
    objects = []
    for fn in files:
        fp = os.path.join(base_dir, fn)
        with open(fp, 'rb') as f:
            objects.append(f.read())
    return objects
