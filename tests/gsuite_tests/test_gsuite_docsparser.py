from nose import SkipTest

from tests.gsuite_tests import get_driver, check_recover_objects

driver = get_driver('document')

# noinspection PyClassHasNoInit
class TestLogMsg:
    def test_log_msg(self):
        # assert_equal(expected, log_msg(cls, msg, error_level))
        raise SkipTest  # TODO: implement your test here


# noinspection PyClassHasNoInit
class TestInsert:
    def test_insert(self):
        # assert_equal(expected, insert(old_string, new_string, index))
        raise SkipTest  # TODO: implement your test here


# noinspection PyClassHasNoInit
class TestDelete:
    def test_delete(self):
        # assert_equal(expected, delete(old_string, starting_index, ending_index))
        raise SkipTest  # TODO: implement your test here


# noinspection PyClassHasNoInit
class TestDocsParser:
    def test___init__(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        raise SkipTest  # TODO: implement your test here

    def test_recover_objects(self):
        # sample = driver.choice.title
        # log = driver.get_log(start=1, end=driver.choice.max_revs)
        # flat_log = driver.flatten_log(log)
        # objects = [(o.filename, o.content) for o in driver.recover_objects(log=log, flat_log=flat_log,
        #                                                                    choice=driver.choice)]
        # hashes = hash_sample_images(sample)
        # for fn, content in objects:
        #     if fn.endswith('.txt'):
        #         yield check_doc, fn, content, sample
        #     else:
        #         yield check_img, fn, content, hashes
        check_recover_objects(driver)

    def test_create_obj_list(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.create_obj_list(objects, type_))
        raise SkipTest  # TODO: implement your test here

    def test_find_sugg_by_index(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.find_sugg_by_index(line_dict, suggestions))
        raise SkipTest  # TODO: implement your test here

    def test_flatten_mts(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.flatten_mts(entry, line_copy, line))
        raise SkipTest  # TODO: implement your test here

    def test_get_comments(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.get_comments(file_choice))
        raise SkipTest  # TODO: implement your test here

    def test_get_doc_objects(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.get_doc_objects(flat_log))
        raise SkipTest  # TODO: implement your test here

    def test_get_drawings(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.get_drawings(drawing_ids, drive, get_download_ext))
        raise SkipTest  # TODO: implement your test here

    def test_get_images(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.get_images(image_ids, get_download_ext, file_choice))
        raise SkipTest  # TODO: implement your test here

    def test_get_log(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.get_log(start, end, choice))
        raise SkipTest  # TODO: implement your test here

    def test_get_plain_text(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.get_plain_text(flat_log))
        raise SkipTest  # TODO: implement your test here

    def test_get_snapshot_line(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.get_snapshot_line(snapshot_entry))
        raise SkipTest  # TODO: implement your test here

    def test_has_drawing(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.has_drawing(elem_dict, drawing_ids))
        raise SkipTest  # TODO: implement your test here

    def test_has_element(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.has_element(line_dict))
        raise SkipTest  # TODO: implement your test here

    def test_has_img(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.has_img(elem_dict))
        raise SkipTest  # TODO: implement your test here

    def test_ins_sugg_text(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.ins_sugg_text(line_dict, old_sugg))
        raise SkipTest  # TODO: implement your test here

    def test_is_delete_suggestion(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.is_delete_suggestion(line_dict))
        raise SkipTest  # TODO: implement your test here

    def test_is_insert_suggestion(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.is_insert_suggestion(line_dict))
        raise SkipTest  # TODO: implement your test here

    def test_new_drawing(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.new_drawing(elem_dict))
        raise SkipTest  # TODO: implement your test here

    def test_new_suggestion(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.new_suggestion(line_dict))
        raise SkipTest  # TODO: implement your test here

    def test_parse_log(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.parse_log(c_log))
        raise SkipTest  # TODO: implement your test here

    def test_parse_snapshot(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.parse_snapshot(snapshot))
        raise SkipTest  # TODO: implement your test here

    def test_rename_keys(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.rename_keys(log_dict))
        raise SkipTest  # TODO: implement your test here

    def test_rm_sugg_text(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.rm_sugg_text(line_dict, suggestion))
        raise SkipTest  # TODO: implement your test here

    def test_stringify(self):
        # docs_parser = DocsParser(client, KumoObj, delimiter)
        # assert_equal(expected, docs_parser.stringify(log))
        raise SkipTest  # TODO: implement your test here


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
