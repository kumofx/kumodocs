import unittest

from nose import SkipTest
from nose.tools import eq_, raises

from gsuite.docshandler import *
from tests.gsuite_tests import test_driver

driver = test_driver.load_case('document')


def test_insert():
    eq_('abc', insert('', 'abc', 0, 0))
    eq_('abZc', insert('abc', 'Z', -1, 0))
    eq_('abzZc', insert('abZc', 'z', 2, 0))
    eq_('Aab', insert('ab', 'A', 1, -1))


def test_delete():
    eq_('', delete('abc', 0, 3, 0))
    eq_('ac', delete('abc', 1, 2, 0))
    eq_('', delete('', 0, 2, 0))
    eq_('af', delete('abcdef', 0, -1, 1))
    eq_('ef', delete('abcdef', 0, 4, 0))


@raises(ValueError)
def test_get_dict_valueerror():
    get_dict('abcd|efgh')


def test_get_dict():
    line = 'ab|de|gh|{"a": 1, "b": 2}'
    dict_ = get_dict(line)
    assert isinstance(dict_, dict)
    eq_(dict_['a'], 1)


def test_get_download_ext():
    resp = {'content-disposition': 'inline;filename="hash3_v1_sm.jpg"'}
    eq_('.jpg', get_download_ext(resp))


def create_obj_list():
    obj = namedtuple('obj', 'content extension notused')
    a = obj('obj a', '.tst', 'none')
    b = obj('obj b', '.jpg', 'test2')
    obj_list = create_obj_list(DocsHandler.KumoObj, [a, b], 'test')
    assert isinstance(obj_list, list)
    k0, k1 = obj_list[0], obj_list[1]
    eq_('test0.tst', k0.filename)
    eq_('obj a', k0.content)


def test_has_drawing():
    elem_dict, drawing_ids = {}, []
    eq_(False, has_drawing(elem_dict, drawing_ids))
    elem_dict = {'d_id': u'ssTSY-cZtq8C5S5MHzOJ3Fg'}
    eq_(True, has_drawing(elem_dict, drawing_ids))
    drawing_ids.append(gsuite.Drawing('ssTSY-cZtq8C5S5MHzOJ3Fg', 0, 0))
    eq_(False, has_drawing(elem_dict, drawing_ids))


def test_has_element():
    eq_(False, has_element({}))
    eq_(True, has_element({'epm': {'ee_eo': 1}}))
    eq_(False, has_element({'epm': {'ee_o': 1}}))


def test_has_img():
    eq_(False, has_img({}))
    eq_(True, has_img({'img_cosmoId'}))


class TestSuggestionFuncs():
    def setUp(self):
        self.sugg = DocsHandler.Suggestion(sug_id='abc', content='test', start=1, end=4, deleted=[])
        self.line_dict = {'sug_id': 'abc', 'string': 'test', 'ins_index': 1}

    def test_is_insert_suggestion(self):
        # 'type' has already been checked to exist
        d = {'type': 'is'}
        eq_(False, is_insert_suggestion(d))
        d = {'type': 'iss'}
        eq_(True, is_insert_suggestion(d))
        d = {'type': 'dss'}
        eq_(False, is_insert_suggestion(d))

    def test_is_delete_suggestion(self):
        # 'type' has already been checked to exist
        d = {'type': 'ds'}
        eq_(False, is_delete_suggestion(d))
        d = {'type': 'iss'}
        eq_(False, is_delete_suggestion(d))
        d = {'type': 'dss'}
        eq_(True, is_delete_suggestion(d))

    @raises(KeyError)
    def test_new_suggestion_raises_keyerror(self):
        new_suggestion({})

    def test_new_suggestion(self):
        eq_(self.sugg, new_suggestion(self.line_dict))

    def test_ins_sugg_text(self):
        new_sugg = DocsHandler.Suggestion(sug_id='abc', content='testtest', start=1, end=8, deleted=[])
        eq_(new_sugg, ins_sugg_text(self.line_dict, self.sugg))

    def test_rm_sugg_text(self):
        new_sugg = DocsHandler.Suggestion(sug_id='abc', content='t', start=1, end=1, deleted=['est'])
        self.line_dict['start_index'], self.line_dict['end_index'] = 2, 4
        eq_(new_sugg, rm_sugg_text(self.line_dict, self.sugg))

    def test_find_sugg_by_index_finds_suggestion(self):
        line_dict = {u'type': u'dss', u'start_index': 148, u'end_index': 164}
        suggestions = {'sugid1': DocsHandler.Suggestion(148, 164, 'abc', 'no content', []),
                       'sugid2': DocsHandler.Suggestion(165, 178, 'abc2', 'def', [])}
        eq_(suggestions['sugid1'], find_sugg_by_index(line_dict, suggestions))

    def test_find_sugg_by_index_no_suggestion(self):
        line_dict = {u'type': u'dss', u'start_index': 148, u'end_index': 164}
        suggestions = {'sugid1': DocsHandler.Suggestion(130, 147, 'abc', 'no content', []),
                       'sugid2': DocsHandler.Suggestion(149, 163, 'abc2', 'def', [])}
        eq_(None, find_sugg_by_index(line_dict, suggestions))


@raises(KeyError)
def test_new_drawing_raises_keyerror():
    new_drawing({})


def test_new_drawing():
    drawing = gsuite.Drawing('abc12', 5, 15)
    elem_dict = {'d_id': 'abc12', 'img_wth': '5', 'img_ht': 15}
    eq_(drawing, new_drawing(elem_dict))


class TestActionDict():
    def setUp(self):
        self.action_dict = {'type': 'dss', 'ins_index': 4, 'string': 'abcdef', 'start_index': 2, 'end_index': 3}

    def test_has_insert_action(self):
        eq_(False, has_insert_action(self.action_dict))
        self.action_dict['type'] = 'iss'
        eq_(True, has_insert_action(self.action_dict))

    def test_has_delete_action(self):
        eq_(True, has_delete_action(self.action_dict))
        self.action_dict['type'] = 'iss'
        eq_(False, has_delete_action(self.action_dict))

    def test_insert_text(self):
        eq_('catabcdefdog', insert_text(self.action_dict, 'catdog'))

    def test_delete_text(self):
        eq_('cdog', delete_text(self.action_dict, 'catdog'))


# noinspection PyClassHasNoInit
class TestDocsHandler:
    def setUp(self):

        self.handler = driver.parser

    def test_parsers(self):
        parsers = {p.__class__.__name__ for p in self.handler.parsers}
        expected = {p.__name__ for p in (self.handler.LogParser, self.handler.FlatParser, CommentsParser,
                                         DrawingsParser, ImageParser, PlaintextParser, SuggestionParser)}
        eq_(expected, parsers)

    def test_logger(self):
        eq_(True, isinstance(self.handler.logger, logging.Logger))

    def test___init__(self):
        # docs_parser = DocsHandler(client, KumoObj, delimiter)
        docs_parser = DocsHandler(self.handler.client)
        eq_(docs_parser.client, self.handler.client)
        eq_(docs_parser.delimiter, Handler.DELIMITER)
        eq_(docs_parser.parser_opt_args, {})
        eq_(True, docs_parser.parsers is not None)

    def test_parser_opts(self):
        flat_log = driver.flat_log
        opts = self.handler.parser_opts(log=None, flat_log=flat_log, choice=None)
        expected = \
            {'image_ids': {'1bolXg367NgeupsiDXAiAx5wfRNAky5P3LTk_0d8', '1SvX-I-GudRP2GqbRsdmhmZIeSqszpqxw2kpFmhk',
                           '1cQTaNyeZeHYN44H7b6bv_eAhh6YecarV475YWK4', '1Vr8y2iC68Nij4ategyBqoh4iVE5jslngevD2g7A',
                           '1s_e_THIKMaD0yw4vgOAGqrw_Nquf0OkYUXL6wW4', '1Z2Zo3QzsaactBwZeNWmQxf4fgIloui9wXHAPNyo',
                           '1QJGug5MnfcQcxQTxMm1muQmqVH42tgP1T1rxGp4'},
             'suggestions': self.handler.KumoObj(filename='suggestions.txt',
                                                 content='{"suggest.zgic4a7zb5zf": [37, 60, "suggest.zgic4a7zb5zf", '
                                                         '"Line added by suggestion", []], "suggest.zcyoau6se2vd": '
                                                         '[104, 103, "suggest.zcyoau6se2vd", "", ["\\n\\n"]]}'),
             'drawing_ids': [gsuite.Drawing(d_id='sqiFH3DuYjX0kc28Etpi1Ww', width=433, height=51)]}
        eq_(expected, opts)

    def test_parse_log_and_snapshot(self):
        expected = []
        expected.extend(self.handler.parse_snapshot(driver.log['chunkedSnapshot']))
        expected.extend(self.handler.parse_log(driver.log['changelog']))
        self.is_flat_log_equal(expected=expected, actual=driver.flat_log)

    def is_flat_log_equal(self, expected, actual):
        """ Dictionaries at the end of flat_log may be in different orders"""
        assert len(expected) == len(actual)
        for e, a in zip(expected, actual):
            eq_(self.make_snapshot_line(e), self.make_snapshot_line(a))

    def make_snapshot_line(self, line):
        line_list = line.split(self.handler.delimiter)
        line_list[-1] = json.loads(line_list[-1])
        return line_list

    def test_flatten_mts(self):
        actual = []
        line = ['timestamp', 'user_id', 'rev_num', None, None]
        entry = self.make_mts_entry()
        expected = self.make_flat_entry()
        self.handler.flatten_mts(entry, actual, line)
        eq_(actual, expected)

    def test_recover_objects(self):
        for obj_test in driver.check_recover_objects():
            yield obj_test

    def make_mts_entry(self):
        mts = [{u'si': 1, u'ty': u'as', u'ei': 1, u'sm': {u'ps_sd_i': True, u'ps_sm_i': True, u'ps_kwn_i': True}},
               {u'si': 0, u'ty': u'as', u'ei': 0, u'sm': {u'lgs_l': u'en'}, u'st': u'language'},
               {u'si': 0, u'ty': u'as', u'ei': 1,
                u'sm': {u'ts_it_i': True, u'ts_st_i': True, u'ts_fgc_i': True, u'ts_bd_i': True, u'ts_fs_i': True,
                        u'ts_un_i': True, u'ts_ff_i': True, u'ts_va_i': True, u'ts_bgc_i': True, u'ts_sc_i': True},
                u'st': u'text'}]
        entry = {'ty': 'mlti', 'mts': mts}
        return entry

    def make_flat_entry(self):
        flat_entry = [['timestamp', 'user_id', 'rev_num', None, None, 'adj_style', '{"start_index": 1, "end_index": 1, '
                                                                                   '"style_mod": {"ps_sd_i": true, "ps_style_i": true, "ps_kwn_i": true}, "type": "as"}'],
                      ['timestamp', 'user_id', 'rev_num', None, None, 'adj_style',
                       '{"start_index": 0, "style_type": "language", "end_index": 0, "style_mod": '
                       '{"language": "en"}, "type": "as"}'],
                      ['timestamp', 'user_id', 'rev_num', None, None, 'adj_style',
                       '{"start_index": 0, "style_type": "text", "end_index": 1, "style_mod": {"underline_i": true, '
                       '"italic_i": true, "strikethrough_i": true, "foreground_color_i": true, "font_family_i": true, '
                       '"vert_align_i": true, "bold_i": true, "font_size_i": true, "background_color_i": true, '
                       '"small_caps_i": true}, "type": "as"}']]
        return flat_entry

    def test_rename_keys(self):
        test_dict = {'si': 1, 'ei': 1, 'sm': {'ps_sd_i': True, 'ps_sm_i': True}}
        expected = OrderedDict([('start_index', 1), ('end_index', 1), ('style_mod', OrderedDict([('ps_sd_i', True),
                                                                                                 ('ps_style_i',
                                                                                                  True)]))])
        actual = self.handler.rename_keys(test_dict)
        assert isinstance(actual, dict)
        assert isinstance(actual['style_mod'], dict)
        eq_(expected, actual)

    def test_get_snapshot_line(self):
        snapshot_entry = driver.log['chunkedSnapshot'][0][0]  # first line in flat_log after heading
        line = driver.delimiter.join(str(item) for item in self.handler.get_snapshot_line(snapshot_entry))
        flat_log_line = driver.flat_log[1]  # first line in flat_log after heading
        eq_(self.make_snapshot_line(line), self.make_snapshot_line(flat_log_line))

    def test_get_doc_objects(self):
        image_ids, drawing_ids, sugg_obj = self.handler.get_doc_objects(driver.flat_log[:131])
        expected_imids = {'1bolXg367NgeupsiDXAiAx5wfRNAky5P3LTk_0d8', '1SvX-I-GudRP2GqbRsdmhmZIeSqszpqxw2kpFmhk',
                          '1cQTaNyeZeHYN44H7b6bv_eAhh6YecarV475YWK4', '1Vr8y2iC68Nij4ategyBqoh4iVE5jslngevD2g7A',
                          '1s_e_THIKMaD0yw4vgOAGqrw_Nquf0OkYUXL6wW4', '1Z2Zo3QzsaactBwZeNWmQxf4fgIloui9wXHAPNyo',
                          '1QJGug5MnfcQcxQTxMm1muQmqVH42tgP1T1rxGp4'}
        expected_dids = [gsuite.Drawing(d_id=u'sqiFH3DuYjX0kc28Etpi1Ww', width=433, height=51)]
        expected_sugg = self.handler.KumoObj(filename='suggestions.txt',
                                             content='{"suggest.zgic4a7zb5zf": [37, 60, ''"suggest.zgic4a7zb5zf", '
                                                     '"Line added by suggestion", []], "suggest.zcyoau6se2vd": [104, 103, '
                                                     '"suggest.zcyoau6se2vd", "", ["\\n\\n"]]}')
        eq_(image_ids, expected_imids)
        eq_(drawing_ids, expected_dids)
        eq_(sugg_obj, expected_sugg)


# noinspection PyClassHasNoInit
class TestCommentsParser:
    def test___init__(self):
        # comments_parser = CommentsParser(service)
        raise SkipTest  # TODO: implement your test here

    def test_get_comments(self):
        # comments_parser = CommentsParser(service)
        # assert_equal(expected, comments_parser.get_comments(file_id))
        raise SkipTest  # TODO: implement your test here


# noinspection PyClassHasNoInit
class TestImageParser:
    def test___init__(self):
        # image_parser = ImageParser(service)
        raise SkipTest  # TODO: implement your test here

    def test_form_render_url(self):
        # image_parser = ImageParser(service)
        # assert_equal(expected, image_parser.form_render_url(file_id, drive))
        raise SkipTest  # TODO: implement your test here

    def test_get_image_links(self):
        # image_parser = ImageParser(service)
        # assert_equal(expected, image_parser.get_image_links(image_ids, file_id, drive))
        raise SkipTest  # TODO: implement your test here

    def test_get_images(self):
        # image_parser = ImageParser(service)
        # assert_equal(expected, image_parser.get_images(image_ids, file_id, drive, get_download_ext))
        raise SkipTest  # TODO: implement your test here

    def test_get_render_request(self):
        # image_parser = ImageParser(service)
        # assert_equal(expected, image_parser.get_render_request(image_ids, file_id, drive))
        raise SkipTest  # TODO: implement your test here


# noinspection PyClassHasNoInit
class TestSuggestionParser:
    def test___init__(self):
        # suggestion_parser = SuggestionParser(service)
        raise SkipTest  # TODO: implement your test here


# noinspection PyClassHasNoInit
class TestDrawingsParser:
    def test___init__(self):
        # drawings_parser = DrawingsParser(service)
        raise SkipTest  # TODO: implement your test here

    def test_get_drawings(self):
        # drawings_parser = DrawingsParser(service)
        # assert_equal(expected, drawings_parser.get_drawings(drawing_ids, drive, get_download_ext))
        raise SkipTest  # TODO: implement your test here


# noinspection PyClassHasNoInit
class TestPlaintextParser:
    def test___init__(self):
        # plaintext_parser = PlaintextParser()
        raise SkipTest  # TODO: implement your test here

    def test_get_dict(self):
        # plaintext_parser = PlaintextParser()
        # assert_equal(expected, plaintext_parser.get_dict(line))
        raise SkipTest  # TODO: implement your test here

    def test_get_plain_text(self):
        # plaintext_parser = PlaintextParser()
        # assert_equal(expected, plaintext_parser.get_plain_text(flat_log))
        raise SkipTest  # TODO: implement your test here


if __name__ == '__main__':
    unittest.main()
