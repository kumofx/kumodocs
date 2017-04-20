import json
import logging
import urllib
from collections import OrderedDict, namedtuple

import gsuite
import mappings

DELIMITER = '|'


# TODO refactor all service requests to gapiclient

# module level functions
def log_msg(cls, msg, error_level):
    """
    Module-level method logs msg with given error_lvl to a logger created with cls name.  
    :param cls: Instance of class object calling the logger
    :param msg: Message to log 
    :param error_level Error level to log message at
    :return: None
    """
    logger = logging.getLogger(cls.__class__.__name__)
    log_func = getattr(logger, error_level)
    log_func(msg)


def insert(old_string, new_string, index):
    """ inserts string new into string old at position i"""
    # in log, index starts at 1
    index -= 1
    return old_string[:index] + new_string + old_string[index:]


def delete(old_string, starting_index, ending_index):
    """ Removes portion from old_string from starting_index to ending_index"""
    # in log, index starts at 1
    starting_index -= 1
    return old_string[:starting_index] + old_string[ending_index:]


class DocsParser(object):
    Suggestion = namedtuple('Suggestion', 'start, end, sug_id, content deleted')

    # Drawing = namedtuple('Drawing', 'd_id width height')

    def __init__(self, client, choice, delimiter='|'):
        self.log = None
        self.flat_log = None
        self.delimiter = delimiter
        self.client = client
        self.service = client.service  # api service
        self.file_choice = choice

        # parsers TODO: refactor to list that executes each using self.flat_log
        self.comments_parser = CommentsParser(self.service)
        self.suggestion_parser = SuggestionParser(self.service)
        self.image_parser = ImageParser(self.service)
        self.drawing_parser = DrawingsParser(self.service)
        self.pt_parser = PlaintextParser()

    def parse_log(self, c_log, flat_log):
        """parses changelog part of log"""

        flat_log.append('changelog')
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

    def parse_snapshot(self, snapshot, flat_log):
        """parses snapshot part of log"""

        flat_log.append('chunkedSnapshot')
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
            flat_log.append(DELIMITER.join(str(item) for item in line))

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
        log_msg(self, 'Recovering image_ids, drawing_ids, and suggestions', 'info')
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
                if self.has_element(line_dict):
                    elem_dict = line_dict['epm']['ee_eo']
                    if self.has_img(elem_dict):
                        image_ids.add(elem_dict['img_cosmoId'])
                    elif self.has_drawing(elem_dict, drawing_ids):
                        drawing_ids.append(self.new_drawing(elem_dict))
                elif 'type' in line_dict:
                    if self.is_insert_suggestion(line_dict):
                        sug_id = line_dict['sug_id']
                        if sug_id in suggestions:
                            suggestions[sug_id] = self.ins_sugg_text(line_dict, suggestions[sug_id])
                        else:
                            suggestions[sug_id] = self.new_suggestion(line_dict)
                    elif self.is_delete_suggestion(line_dict):
                        suggestion = self.find_sugg_by_index(line_dict, suggestions)
                        if suggestion:
                            suggestions[suggestion.sug_id] = self.rm_sugg_text(line_dict, suggestion)

        return image_ids, drawing_ids, suggestions

    def has_drawing(self, elem_dict, drawing_ids):
        """ True if elem_dict has drawing not contained in drawing_ids already """
        return 'd_id' in elem_dict and not any(d for d in drawing_ids if d.d_id == elem_dict['d_id'])

    def has_element(self, line_dict):
        return 'epm' in line_dict and 'ee_eo' in line_dict['epm']

    def has_img(self, elem_dict):
        return 'img_cosmoId' in elem_dict

    def is_insert_suggestion(self, line_dict):
        return line_dict['type'] == 'iss'

    def is_delete_suggestion(self, line_dict):
        return line_dict['type'] == 'dss'

    def new_suggestion(self, line_dict):
        """ Returns a new Suggestion with sug_id, content, start index, end index, deleted chars"""
        sug_id, content, start = line_dict['sug_id'], line_dict['string'], line_dict['ins_index']
        end = start + len(content) - 1
        return DocsParser.Suggestion(sug_id=sug_id, content=content, start=start, end=end, deleted=[])

    def ins_sugg_text(self, line_dict, old_sugg):
        """ Returns new Suggestion with text inserted at the appropriate index """
        relative_index = line_dict['ins_index'] - old_sugg.start + 1  # index start @1 in log
        new_text = insert(old_string=old_sugg.content, new_string=line_dict['string'],
                          index=relative_index)
        return DocsParser.Suggestion(sug_id=old_sugg.sug_id, content=new_text, start=old_sugg.start,
                                     end=old_sugg.end + len(line_dict['string']), deleted=old_sugg.deleted)

    def rm_sugg_text(self, line_dict, suggestion):
        """ Returns new Suggestion with all deleted_chr appended to delete and removed from content """
        # normalize indices
        rm_start = line_dict['start_index'] - suggestion.start
        rm_end = line_dict['end_index'] - suggestion.start + 1

        deleted_chr = suggestion.content[rm_start:rm_end]
        new_content = suggestion.content[:rm_start] + suggestion.content[rm_end:]
        new_end = suggestion.end - len(deleted_chr)
        suggestion.deleted.append(deleted_chr)

        return DocsParser.Suggestion(sug_id=suggestion.sug_id, start=suggestion.start, end=new_end,
                                     content=new_content, deleted=suggestion.deleted)

    def find_sugg_by_index(self, line_dict, suggestions):
        """ Searches for Suggestion that contains start_index in its [start,end] range """
        suggestion = [s for s in suggestions.values() if s.start <= line_dict['start_index'] <= s.end]
        if len(suggestion) == 1:
            return suggestion[0]
        elif len(suggestion) > 1:
            log_msg(cls=self, msg='too many suggestions', error_level='debug')
            return suggestion[0]
        else:
            log_msg(cls=self, msg='could not find suggestion \n line dict = {}\n suggestions= {}'.format(line_dict,
                                                                                                         suggestions),
                    error_level='debug')
            return None

    def new_drawing(self, elem_dict):
        """ Returns a new Drawing namedtuple containing id, width, and height """
        drawing_keys = ('d_id', 'img_wth', 'img_ht')
        d_id, img_wth, img_ht = (elem_dict[key] for key in drawing_keys)
        return gsuite.Drawing(d_id, int(img_wth), int(img_ht))

    def get_comments(self):
        log_msg(self, 'Retrieving comments', 'info')
        return self.comments_parser.get_comments(self.file_choice.file_id)

    def get_images(self, image_ids, get_download_ext):
        log_msg(self, 'Retrieving images', 'info')
        return self.image_parser.get_images(image_ids=image_ids, file_id=self.file_choice.file_id,
                                            drive=self.file_choice.drive, get_download_ext=get_download_ext)

    def get_drawings(self, drawing_ids, drive, get_download_ext):
        log_msg(self, 'Retrieving drawings', 'info')
        return self.drawing_parser.get_drawings(drawing_ids=drawing_ids, drive=drive, get_download_ext=get_download_ext)

    def get_plain_text(self, flat_log):
        log_msg(self, 'Recovering plain text', 'info')
        return self.pt_parser.get_plain_text(flat_log=flat_log)


class CommentsParser(object):
    """ Methods to recover comments from log"""

    def __init__(self, service):
        self.service = service

    def get_comments(self, file_id):
        """ Gets comments and replies to those comments, and metadata for deleted comments """

        reply_fields = 'author, content, createdDate, modifiedDate, deleted'
        comment_fields = 'items(status, author, content, createdDate, modifiedDate, deleted, ' \
                         'replies({}))'.format(reply_fields)

        # output templates for comments and replies
        comment_template = '{num}. comment: {content} \nauthor: {author[displayName]}, ' \
                           'status: {status}, created: {createdDate}, modified: {modifiedDate}, ' \
                           'deleted: {deleted} \nreplies:'
        reply_template = '\n\t({num}) reply: {content} \n\tauthor: {author[displayName]}, ' \
                         'created: {createdDate}, modified: {modifiedDate}, deleted: {deleted}'

        contents = self.service.comments().list(fileId=file_id, includeDeleted=True,
                                                fields=comment_fields).execute()
        contents = contents['items']

        comments = []
        for i, comment in enumerate(contents):
            comment['num'] = i + 1
            comments.append(comment_template.format(**comment))
            for j, reply in enumerate(comment['replies']):
                reply['num'] = j + 1
                if 'content' in reply.keys():
                    comments.append(reply_template.format(**reply))
                else:
                    reply['content'] = ''
                    comments.append(reply_template.format(**reply))
            comments.append('\n\n')
        return comments


class ImageParser(object):
    """ Methods to recover images from log """

    # TODO refactor api logic to gapiclient

    def __init__(self, service):
        self.service = service

    def get_images(self, image_ids, file_id, drive, get_download_ext):
        """ Gets a list of links and resolves each one, returning a list of tuples containing
        (image, extension, img_id) for each image resource"""
        images = []
        links = self.get_image_links(image_ids=image_ids, file_id=file_id, drive=drive)
        for url, img_id in links.itervalues():
            try:
                response, content = self.service._http.request(url)
            except:
                log_msg(cls=self, msg='Image could not be retrieved:\n\turl={}\n\t'
                                      'img_id={}'.format(url, img_id), error_level='debug')
            else:
                extension = get_download_ext(response)
                images.append((content, extension, img_id))

        return images

    def get_image_links(self, image_ids, file_id, drive):
        """ Sends url request to google API which returns a link for each image resource, returns
        dictionary of tuples containing those links along with each image_id associated with link"""
        render_url, request_body, my_headers = self.get_render_request(image_ids=image_ids, file_id=file_id,
                                                                       drive=drive)
        try:
            response, content = self.service._http.request(render_url, method='POST',
                                                           body=request_body, headers=my_headers)
        except:
            log_msg(cls=self, msg='Renderdata url cannot be resolved:\n\trender_url={}\n\t'
                                  'body={}'.format(render_url, request_body), error_level='debug')
        else:
            content = json.loads(content[5:])
            # keep assocation of image ids with image
            for i, img_id in enumerate(image_ids):
                key = 'r' + str(i)
                content[key] = (content.pop(key), img_id)
            return content

    def get_render_request(self, image_ids, file_id, drive):
        """ Returns url request to retrieve images with image_ids contained in file with file_id"""

        image_ids = set(image_ids)
        data = {}
        for i, img_id in enumerate(image_ids):
            key = 'r' + str(i)
            # unicode image_ids are not accepted in the request, so they must be encoded as strings
            data[key] = ['image', {'cosmoId': img_id.encode(), 'container': file_id}]
        request_body = urllib.urlencode({'renderOps': data}).replace('+', '')
        my_headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}

        render_url = self.form_render_url(file_id=file_id, drive=drive)

        return render_url, request_body, my_headers

    def form_render_url(self, file_id, drive):
        params = gsuite.RENDER_PARAMS.format(file_id=file_id)
        render_url = gsuite.API_BASE.format(params=params, file_id=file_id, drive=drive)
        return render_url


class SuggestionParser(object):
    """ Methods to recover suggestions from log """

    def __init__(self, service):
        self.service = service


class DrawingsParser(object):
    """ Methods to recover drawings from log """

    def __init__(self, service):
        self.service = service

    def get_drawings(self, drawing_ids, drive, get_download_ext):
        """
        Returns a list of URLs to retrieve drawings in drawing_ids
        :param drawing_ids: A list of drawing_ids retrieved from log 
        :param drive: Location of drawing resource denoted by drive, usually Drawings
        :param get_download_ext: temporary function from gapiclient
        :return: A list of URLs to retrieve the drawings. 
        """

        # TODO get_download_ext -> call from client
        drawings = []
        for drawing in drawing_ids:
            # url = DRAW_PATH.format(d_id=drawing_id[0], w=drawing_id[1], h=drawing_id[2])
            params = gsuite.DRAW_PARAMS.format(w=drawing.width, h=drawing.height)
            url = gsuite.API_BASE.format(params=params, drive=drive, file_id=drawing.d_id)
            response, content = self.service._http.request(url)
            extension = get_download_ext(response)
            drawings.append((content, extension))

        return drawings


class PlaintextParser(object):
    def __init__(self):
        pass

    def get_plain_text(self, flat_log):
        """ converts flat log to plaintext"""
        plain_text = ''
        log_dict = self.get_dict(flat_log[flat_log.index('chunkedSnapshot') + 1])

        # should not contain a string if log starts at revision 1
        if 'string' in log_dict:
            chunk_string = log_dict['string']
            # chunk_string = chunk_string.decode('unicode-escape')
            plain_text += chunk_string

        # start after changelog line, which has no data
        cl_index = flat_log.index('changelog') + 1

        for line in flat_log[cl_index:]:
            try:
                action_dict = self.get_dict(line)

                if action_dict['type'].startswith('is'):
                    i = action_dict['ins_index']
                    s = action_dict['string']
                    plain_text = insert(old_string=plain_text, new_string=s, index=i)

                elif action_dict['type'].startswith('ds'):
                    si = action_dict['start_index']
                    ei = action_dict['end_index']
                    plain_text = delete(old_string=plain_text, starting_index=si, ending_index=ei)
            except ValueError:
                pass

        return plain_text

    def get_dict(self, line):
        """ converts string dictionary at end of line in log to dictionary object"""
        i = line.index('{')
        try:
            log_dict = json.loads(line[i:])
        except ValueError:
            raise  # should not have a line without dictionary
        else:
            return log_dict
