from collections import namedtuple

# package-level constants defined below
API_BASE = 'https://docs.google.com/{drive}/d/{file_id}/{params}'
REV_PARAMS = 'revisions/load?start={start}&end={end}'
RENDER_PARAMS = 'renderdata?id={file_id}'
MIME_TYPE = "mimeType = 'application/vnd.google-apps.{}'"
SERVICES = ['document']  # , 'drawing', 'form', 'presentation', 'spreadsheet']
DRAW_PARAMS = 'image?w={w}&h={h}'
CHUNKED_ORDER = ['si', 'ei', 'st']

# package-level named tuples
FileChoice = namedtuple('FileChoice', 'file_id, title, drive, max_revs')
Drawing = namedtuple('Drawing', 'd_id width height')
