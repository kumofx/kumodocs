import cgi
import json
import logging
import os
import urllib
from collections import OrderedDict, namedtuple

import gsuite
import mappings
from baseclass import Parser, Handler

logger = logging.getLogger(__name__)

INDEX_OFFSET = -1


def insert(old_string, new_string, index, index_offset):
    """ inserts string new into string old at position i"""
    # in log, index starts at 1
    index += index_offset
    return old_string[:index] + new_string + old_string[index:]


def delete(old_string, starting_index, ending_index, index_offset):
    """ Removes portion from old_string from starting_index to ending_index"""
    # in log, index starts at 1
    starting_index += index_offset
    return old_string[:starting_index] + old_string[ending_index:]


def get_dict(line):
    """ converts string dictionary at end of line in log to dictionary object"""
    i = line.index('{')
    try:
        log_dict = json.loads(line[i:])
    except ValueError:
        raise  # should not have a line without dictionary
    else:
        return log_dict


def get_download_ext(html_response):
    """
    Returns extension for downloaded resource as formatted for GSuite API html response
    :param html_response:  GSuite API html response
    :return: Extension of downloaded resource (png, pdf, doc, etc)
    """
    try:
        filename = cgi.parse_header(html_response['content-disposition'])[-1]['filename']
    except KeyError:
        return '.failed'
    else:
        extension = os.path.splitext(filename)[1]
    return extension


def create_obj_list(kumo_obj, objects, type_):
    """
    Creates a list of KumoObj of the appropriate type and content
    :param kumo_obj: KumoObj object
    :param objects: A list of objects with a content property
    :param type_: object type is prepended to the filename
    :return: List of KumoObj
    """
    obj_list = []
    for i, obj in enumerate(objects):
        filename = '{}{}{}'.format(type_, i, obj.extension)
        obj_list.append(kumo_obj(filename=filename, content=obj.content))
    return obj_list


def has_drawing(elem_dict, drawing_ids):
    """ True if elem_dict has drawing not contained in drawing_ids already """
    return 'd_id' in elem_dict and not any(d for d in drawing_ids if d.d_id == elem_dict['d_id'])


def has_element(line_dict):
    return 'epm' in line_dict and 'ee_eo' in line_dict['epm']


def has_img(elem_dict):
    return 'img_cosmoId' in elem_dict


def is_insert_suggestion(line_dict):
    return line_dict['type'] == 'iss'


def is_delete_suggestion(line_dict):
    return line_dict['type'] == 'dss'


def new_suggestion(line_dict):
    """ Returns a new Suggestion with sug_id, content, start index, end index, deleted chars"""
    sug_id, content, start = line_dict['sug_id'], line_dict['string'], line_dict['ins_index']
    end = start + len(content) - 1
    return DocsHandler.Suggestion(sug_id=sug_id, content=content, start=start, end=end, deleted=[])


def ins_sugg_text(line_dict, old_sugg):
    """ Returns new Suggestion with text inserted at the appropriate index """
    relative_index = line_dict['ins_index'] - old_sugg.start + 1  # index start @1 in log
    new_text = insert(old_string=old_sugg.content, new_string=line_dict['string'],
                      index=relative_index, index_offset=INDEX_OFFSET)
    return DocsHandler.Suggestion(sug_id=old_sugg.sug_id, content=new_text, start=old_sugg.start,
                                  end=old_sugg.end + len(line_dict['string']), deleted=old_sugg.deleted)


def rm_sugg_text(line_dict, suggestion):
    """ Returns new Suggestion with all deleted_chr appended to delete and removed from content """
    # normalize indices
    rm_start = line_dict['start_index'] - suggestion.start
    rm_end = line_dict['end_index'] - suggestion.start + 1

    deleted_chr = suggestion.content[rm_start:rm_end]
    new_content = suggestion.content[:rm_start] + suggestion.content[rm_end:]
    new_end = suggestion.end - len(deleted_chr)
    suggestion.deleted.append(deleted_chr)

    return DocsHandler.Suggestion(sug_id=suggestion.sug_id, start=suggestion.start, end=new_end,
                                  content=new_content, deleted=suggestion.deleted)


def find_sugg_by_index(line_dict, suggestions):
    """ Searches for Suggestion that contains start_index in its [start,end] range """
    suggestion = [s for s in suggestions.values() if s.start <= line_dict['start_index'] <= s.end]
    if len(suggestion) == 1:
        return suggestion[0]
    elif len(suggestion) > 1:
        logger.debug('Too many suggestions: {}'.format(suggestion))
        return suggestion[0]
    else:
        logger.debug('Could not find suggestion: \n line dict = {}\n suggestions= {}'.format(line_dict, suggestions))
        return None


def new_drawing(elem_dict):
    """ Returns a new Drawing namedtuple containing id, width, and height """
    drawing_keys = ('d_id', 'img_wth', 'img_ht')
    d_id, img_wth, img_ht = (elem_dict[key] for key in drawing_keys)
    return gsuite.Drawing(d_id, int(img_wth), int(img_ht))


def has_insert_action(action_dict):
    return action_dict['type'].startswith('is')


def has_delete_action(action_dict):
    return action_dict['type'].startswith('ds')


def insert_text(action_dict, plain_text):
    i = action_dict['ins_index']
    s = action_dict['string']
    return insert(old_string=plain_text, new_string=s, index=i, index_offset=INDEX_OFFSET)


def delete_text(action_dict, plain_text):
    si = action_dict['start_index']
    ei = action_dict['end_index']
    return delete(old_string=plain_text, starting_index=si, ending_index=ei, index_offset=INDEX_OFFSET)


class DocsHandler(Handler):
    @property
    def parsers(self):
        return self._parsers

    @property
    def logger(self):
        return logger

    def __init__(self, client, delimiter=None, parsers=None):
        super(DocsHandler, self).__init__(client, delimiter)
        self._parsers = [self.init_parser(p) for p in parsers or self.collect_parsers(__name__)]

    Suggestion = namedtuple('Suggestion', 'start, end, sug_id, content deleted')

    # Drawing = namedtuple('Drawing', 'd_id width height')

    def parser_opts(self, log, flat_log, choice):
        """ Additional arguments get sent to each parser's parse() function"""
        image_ids, drawing_ids, suggestions = self.get_doc_objects(flat_log=flat_log)
        return {'image_ids': image_ids, 'drawing_ids': drawing_ids, 'suggestions': suggestions}

    def parse_log(self, c_log):
        """parses changelog part of log"""

        flat_log = ['changelog{}{}'.format(self.delimiter, '{}')]
        for entry in c_log:
            action_dict = entry[0]
            ts_id_info = entry[1:-1]
            line = ts_id_info

            # break up multiset into components
            if 'mts' in action_dict:
                line_copy = []
                self.flatten_mts(action_dict, line_copy, line)
                for item in line_copy:
                    flat_log.append(self.delimiter.join(str(col) for col in item))
            else:
                action_type = mappings.remap(action_dict['ty'])
                line.append(action_type)
                line.append(json.dumps(self.rename_keys(action_dict)))
                flat_log.append(self.delimiter.join(str(item) for item in line))

        return flat_log

    def parse_snapshot(self, snapshot):
        """parses snapshot part of log"""

        flat_log = ['chunkedSnapshot{}{}'.format(self.delimiter, '{}')]
        snapshot = snapshot[0]

        # take care of plain text paste entry
        if 's' in snapshot[0]:
            snapshot[0]['type'] = snapshot[0].pop('ty')
            snapshot[0]['string'] = snapshot[0].pop('s').replace('\n', '\\n')
            del snapshot[0]['ibi']  # this value is always 1 and unused
            flat_log.append(json.dumps(snapshot.pop(0)))  # pop entry to remove special case

        # parse style modifications
        for entry in snapshot:
            line = self.get_snapshot_line(snapshot_entry=entry)
            flat_log.append(self.delimiter.join(str(item) for item in line))

        return flat_log

    def flatten_mts(self, entry, line_copy, line):
        """ Recursively flatten multiset entry.

      Args:
        entry: an entry in changelog
        line_copy: a flattened list of each mts action appended to line
        line:  shared info for the entry( id, revision, timestamp, etc)
      Returns:
        None.  line_copy contains flattened entries to be appended to log.
      """
        if 'mts' not in entry:
            new_line = list(line)
            mts_action = mappings.remap(entry['ty'])

            # add action & action dictionary with descriptive keys
            new_line.append(mts_action)
            new_line.append(json.dumps(self.rename_keys(entry)))
            line_copy.append(new_line)

        else:
            for item in entry['mts']:
                self.flatten_mts(item, line_copy, line)

    def rename_keys(self, log_dict):
        """rename minified variables using mappings in `mappings.py`. preserves order"""
        log_dict = OrderedDict(log_dict)
        for key in log_dict.keys():
            try:
                new_key = mappings.remap(key)
                log_dict[new_key] = log_dict.pop(key)

                # recursively replace deep dictionaries
                if isinstance(log_dict[new_key], dict):
                    log_dict[new_key] = self.rename_keys(log_dict[new_key])
            except KeyError:
                # if key is not in mappings, leave old key unchanged.
                pass

        return log_dict

    def get_snapshot_line(self, snapshot_entry):
        """
        Turns raw line from snapshot into a translated version for flat_log with style dictionary at end
        :param snapshot_entry: A line in the snapshot part of the log
        :return: line entry for flat_log with style dictionary at end
        """
        line = []
        for key in gsuite.CHUNKED_ORDER:
            line.append(snapshot_entry[key])

        action_type = mappings.remap(snapshot_entry['ty'])
        style_mod = json.dumps(self.rename_keys(snapshot_entry['sm']))
        line.append(action_type)
        line.append(style_mod)

        return line

    def get_doc_objects(self, flat_log):
        """
        Discovers objects from flat_log in a single pass.
        :param flat_log: preprocessed version of google changelog
        :return: list of comment_anchors, image_ids, drawing_ids, and a suggestions dictionary
        """
        logger.info('Recovering image_ids, drawing_ids, and suggestions')
        image_ids = set()
        drawing_ids = []
        suggestions = {}

        for line in flat_log:
            try:
                i = line.index('{')
                line_dict = json.loads(line[i:])
            except ValueError:
                pass  # either chunked or changelog header without dict, no action needed
            else:
                if has_element(line_dict):
                    elem_dict = line_dict['epm']['ee_eo']
                    if has_img(elem_dict):
                        image_ids.add(elem_dict['img_cosmoId'])
                    elif has_drawing(elem_dict, drawing_ids):
                        drawing_ids.append(new_drawing(elem_dict))
                elif 'type' in line_dict:
                    if is_insert_suggestion(line_dict):
                        sug_id = line_dict['sug_id']
                        if sug_id in suggestions:
                            suggestions[sug_id] = ins_sugg_text(line_dict, suggestions[sug_id])
                        else:
                            suggestions[sug_id] = new_suggestion(line_dict)
                    elif is_delete_suggestion(line_dict):
                        suggestion = find_sugg_by_index(line_dict, suggestions)
                        if suggestion:
                            suggestions[suggestion.sug_id] = rm_sugg_text(line_dict, suggestion)

        sugg_obj = self.KumoObj(filename='suggestions.txt', content=json.dumps(suggestions, ensure_ascii=False))
        return image_ids, drawing_ids, sugg_obj


class CommentsParser(Parser):
    """ Methods to recover comments from log"""

    @property
    def logger(self):
        return logger

    def parse(self, log, flat_log, choice, **kwargs):
        self.logger.info('Retrieving comments')
        comments = '\n'.join(str(line) for line in self.get_comments(choice.file_id))
        comment_obj = self.KumoObj(filename='comments.txt', content=comments)
        return comment_obj

    def get_comments(self, file_id):
        """ Fetches comments,replies, metadata, and formats according to format_contents """

        comments = self.client.fetch_comments(file_id, self.comment_fields())
        return self.format_comments(comments)

    def format_comments(self, contents):
        """ Applies templates to each comment and each reply in contents """
        comment_template, reply_template = self.format_templates()
        comments = []
        for i, comment in enumerate(contents):
            comment['num'] = i + 1
            comments.append(comment_template.format(**comment))
            for j, reply in enumerate(comment['replies']):
                reply['num'] = j + 1
                if 'content' not in reply.keys():
                    reply['content'] = ''
                comments.append(reply_template.format(**reply))
            comments.append('\n\n')

        return comments

    @staticmethod
    def comment_fields():
        """ Restricts return data from API to specified attributes """

        reply_fields = 'author, content, createdDate, modifiedDate, deleted'
        comment_fields = 'items(status, author, content, createdDate, modifiedDate, deleted, ' \
                         'replies({}))'.format(reply_fields)

        return comment_fields

    @staticmethod
    def format_templates():
        """ Returns output templates for comment and reply formatting """

        comment_template = '{num}. comment: {content} \nauthor: {author[displayName]}, ' \
                           'status: {status}, created: {createdDate}, modified: {modifiedDate}, ' \
                           'deleted: {deleted} \nreplies:'
        reply_template = '\n\t({num}) reply: {content} \n\tauthor: {author[displayName]}, ' \
                         'created: {createdDate}, modified: {modifiedDate}, deleted: {deleted}'

        return comment_template, reply_template


class ImageParser(Parser):
    """ Methods to recover images from log """

    @property
    def logger(self):
        return logger

    Image = namedtuple('Image', 'content extension img_id')

    def parse(self, log, flat_log, choice, **kwargs):
        image_ids = kwargs.get('image_ids')
        self.logger.info('Retrieving images')
        images = self.get_images(image_ids=image_ids, file_id=choice.file_id,
                                 drive=choice.drive)

        return create_obj_list(self.KumoObj, images, 'img')

    def get_images(self, image_ids, file_id, drive):
        """
        Retrieves images using private API and image_ids
        :param image_ids: Cosmo image IDs retrieved from a Google Docs log
        :param file_id: Unique GSuite file ID
        :param drive: Type of GSuite service
        :return: List of KumoObj with image contents.
        """
        images = []
        links = self.get_image_links(image_ids=image_ids, file_id=file_id, drive=drive)
        if links:
            for url, img_id in links.itervalues():
                try:
                    response, content = self.client.request(url)
                except self.client.HttpError:
                    self.logger.debug('Image could not be retrieved:\n\turl={}\n\t img_id={}'.format(url, img_id))
                else:
                    extension = get_download_ext(response)
                    img = self.Image(content, extension, img_id)
                    images.append(img)

        return images

    def get_image_links(self, image_ids, file_id, drive):
        """ Sends url request to google API which returns a link for each image resource, returns
        dictionary of tuples containing those links along with each image_id associated with link"""
        render_url, request_body, my_headers = self.get_render_request(image_ids=image_ids, file_id=file_id,
                                                                       drive=drive)
        try:
            response, content = self.client.request(render_url, method='POST',
                                                    body=request_body, headers=my_headers)
        except self.client.HttpError:
            self.logger.debug(
                'Renderdata url cannot be resolved:\n\trender_url={}\n\t body={}'.format(render_url, request_body))
            return {}
        else:
            content = json.loads(content[5:])
            # keep association of image ids with image
            for i, img_id in enumerate(image_ids):
                key = 'r' + str(i)
                content[key] = (content.pop(key), img_id)
            return content

    def get_render_request(self, image_ids, file_id, drive):
        """ Returns url request to retrieve images with image_ids contained in file with file_id"""

        image_ids = set(image_ids)
        data = {}
        for i, img_id in enumerate(image_ids):
            key = "r" + str(i)
            # unicode image_ids are not accepted in the request, so they must be encoded as strings
            data[key] = ["image", {"cosmoId": img_id.encode(), "container": file_id}]

        # removes '+' character and changes single to double quotes to prevent bad request
        request_body = urllib.urlencode({"renderOps": data}).replace('+', '').replace('%27', '%22')
        my_headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}

        render_url = self.form_render_url(file_id=file_id, drive=drive)

        return render_url, request_body, my_headers

    @staticmethod
    def form_render_url(file_id, drive):
        params = gsuite.RENDER_PARAMS.format(file_id=file_id)
        render_url = gsuite.API_BASE.format(params=params, file_id=file_id, drive=drive)
        return render_url


class SuggestionParser(Parser):
    """ Methods to recover suggestions from log """

    @property
    def logger(self):
        return logger

    def parse(self, log, flat_log, choice, **kwargs):
        """ Suggestions are recovered in `DocsHandler.get_doc_objects` """
        suggestions = kwargs.get('suggestions', [])
        return suggestions


class DrawingsParser(Parser):
    """ Methods to recover drawings from log """

    @property
    def logger(self):
        return logger

    Drawing = namedtuple('Drawing', 'content extension')

    def parse(self, log, flat_log, choice, **kwargs):
        self.logger.info('Retrieving drawings')
        drawing_ids = kwargs.get('drawing_ids')
        drawings = self.get_drawings(drawing_ids=drawing_ids, drive='Drawing')

        return create_obj_list(self.KumoObj, drawings, 'drawing')

    def get_drawings(self, drawing_ids, drive):
        """
        Returns a list Drawings corresponding to drawing_ids recovered from log
        :param drawing_ids: A list of drawing_ids retrieved from log 
        :param drive: Location of drawing resource denoted by drive, usually Drawings
        :return: A list of Drawings with content and extension 
        """

        # TODO get_download_ext -> call from client
        drawings = []
        for drawing in drawing_ids:
            # url = DRAW_PATH.format(d_id=drawing_id[0], w=drawing_id[1], h=drawing_id[2])
            params = gsuite.DRAW_PARAMS.format(w=drawing.width, h=drawing.height)
            url = gsuite.API_BASE.format(params=params, drive='drawings', file_id=drawing.d_id)

            try:
                response, content = self.client.request(url)
            except self.client.HttpError:
                self.logger.info('Could not retrieve Drawing id {}'.format(drawing.d_id))
            else:
                extension = get_download_ext(response)
                drawings.append(self.Drawing(content, extension))

        return drawings


class PlaintextParser(Parser):
    """ Methods to recover plain text from log """

    @property
    def logger(self):
        return logger

    def parse(self, log, flat_log, choice, **kwargs):
        self.logger.info('Recovering plain text')
        plain_text = self.get_plain_text(flat_log=flat_log)
        pt_obj = self.KumoObj(filename='plaintext.txt', content=plain_text.encode('utf-8'))
        return [pt_obj]

    def get_plain_text(self, flat_log):
        """ converts flat log to plaintext"""
        plain_text = ''
        snapshot_line = 'chunkedSnapshot{}{}'.format(self.delimiter, '{}')
        changelog_line = 'changelog{}{}'.format(self.delimiter, '{}')
        log_dict = get_dict(flat_log[flat_log.index(snapshot_line) + 1])

        # should not contain a string if log starts at revision 1
        if 'string' in log_dict:
            chunk_string = log_dict['string']
            # chunk_string = chunk_string.decode('unicode-escape')
            plain_text += chunk_string

        # start after changelog line, which has no data
        cl_index = flat_log.index(changelog_line) + 1

        for line in flat_log[cl_index:]:
            try:
                action_dict = get_dict(line)
            except ValueError:
                pass
            else:
                if has_insert_action(action_dict):
                    plain_text = insert_text(action_dict, plain_text)

                elif has_delete_action(action_dict):
                    plain_text = delete_text(action_dict, plain_text)

        return plain_text
