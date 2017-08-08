from nose import SkipTest

from tests.gsuite_tests import get_driver, check_recover_objects


# noinspection PyClassHasNoInit
class TestDrawingsParser:
    def test_recover_objects(self):
        # slides_parser = SlidesParser(client, KumoObj, delimiter)
        # assert_equal(expected, slides_parser.recover_objects(log, flat_log, choice))
        driver = get_driver('drawing')
        check_recover_objects(driver)


# noinspection PyClassHasNoInit
class TestSlidesParser:
    def test___init__(self):
        # slides_parser = SlidesParser(client, KumoObj, delimiter)
        raise SkipTest  # TODO: implement your test here

    def test_recover_objects(self):
        driver = get_driver('presentation')
        check_recover_objects(driver)

    def test_create_obj_list(self):
        # slides_parser = SlidesParser(client, KumoObj, delimiter)
        # assert_equal(expected, slides_parser.create_obj_list(objects, type_))
        raise SkipTest  # TODO: implement your test here

    def test_get_comments(self):
        # slides_parser = SlidesParser(client, KumoObj, delimiter)
        # assert_equal(expected, slides_parser.get_comments(file_choice))
        raise SkipTest  # TODO: implement your test here

    def test_get_images(self):
        # slides_parser = SlidesParser(client, KumoObj, delimiter)
        # assert_equal(expected, slides_parser.get_images(image_ids, get_download_ext, file_choice))
        raise SkipTest  # TODO: implement your test here

    def test_get_log(self):
        # slides_parser = SlidesParser(client, KumoObj, delimiter)
        # assert_equal(expected, slides_parser.get_log(start, end, choice))
        raise SkipTest  # TODO: implement your test here

    def test_get_plain_text(self):
        # slides_parser = SlidesParser(client, KumoObj, delimiter)
        # assert_equal(expected, slides_parser.get_plain_text(log))
        raise SkipTest  # TODO: implement your test here

    def test_get_slide_objects(self):
        # slides_parser = SlidesParser(client, KumoObj, delimiter)
        # assert_equal(expected, slides_parser.get_slide_objects(log))
        raise SkipTest  # TODO: implement your test here

    def test_parse_log(self):
        # slides_parser = SlidesParser(client, KumoObj, delimiter)
        # assert_equal(expected, slides_parser.parse_log(c_log))
        raise SkipTest  # TODO: implement your test here

    def test_parse_snapshot(self):
        # slides_parser = SlidesParser(client, KumoObj, delimiter)
        # assert_equal(expected, slides_parser.parse_snapshot(snapshot))
        raise SkipTest  # TODO: implement your test here


# noinspection PyClassHasNoInit
class TestPlainTextParser:
    def test___init__(self):
        # plain_text_parser = PlainTextParser(KumoObj)
        raise SkipTest  # TODO: implement your test here

    def test_get_plain_text(self):
        # plain_text_parser = PlainTextParser(KumoObj)
        # assert_equal(expected, plain_text_parser.get_plain_text(log))
        raise SkipTest  # TODO: implement your test here

    def test_make_pt_obj(self):
        # plain_text_parser = PlainTextParser(KumoObj)
        # assert_equal(expected, plain_text_parser.make_pt_obj(filename, box, box_dict))
        raise SkipTest  # TODO: implement your test here

    def test_write_output(self):
        # plain_text_parser = PlainTextParser(KumoObj)
        # assert_equal(expected, plain_text_parser.write_output(presentation))
        raise SkipTest  # TODO: implement your test here


# noinspection PyClassHasNoInit
class TestPresentation:
    def test___init__(self):
        # presentation = Presentation(log)
        raise SkipTest  # TODO: implement your test here

    def test_add_box(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.add_box(line))
        raise SkipTest  # TODO: implement your test here

    def test_add_slide(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.add_slide(line))
        raise SkipTest  # TODO: implement your test here

    def test_add_text(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.add_text(line))
        raise SkipTest  # TODO: implement your test here

    def test_del_box(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.del_box(line))
        raise SkipTest  # TODO: implement your test here

    def test_del_slide(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.del_slide(line))
        raise SkipTest  # TODO: implement your test here

    def test_del_text(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.del_text(line))
        raise SkipTest  # TODO: implement your test here

    def test_delete(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.delete(old, start, end))
        raise SkipTest  # TODO: implement your test here

    def test_insert(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.insert(old, add, i))
        raise SkipTest  # TODO: implement your test here

    def test_move_slide(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.move_slide(line))
        raise SkipTest  # TODO: implement your test here

    def test_parse(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.parse(data))
        raise SkipTest  # TODO: implement your test here

    def test_parse_line(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.parse_line(line))
        raise SkipTest  # TODO: implement your test here

    def test_parse_mts(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.parse_mts(data))
        raise SkipTest  # TODO: implement your test here

    def test_trim_log(self):
        # presentation = Presentation(log)
        # assert_equal(expected, presentation.trim_log(log))
        raise SkipTest  # TODO: implement your test here
