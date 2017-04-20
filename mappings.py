_MAPPINGS = {
    "ty": "type",
    "st": "style_type",
    "s": "string",
    "ibi": "ins_index",
    "si": "start_index",
    "ei": "end_index",
    "is": "ins",
    "ds": "del",
    "as": "adj_style",
    "fm": "fm",  #
    "timestamp": "timestamp",
    "UID": "UID",
    "rev": "rev",
    "SID": "SID",
    "SRev": "SRev",
    "sm": "style_mod",
    "mts": "multiset",
    "tbs_al": "table_aln",  #
    "tbs_of": "table_off",  #
    "das_a": "ds_anchor",
    "ps_ltr": "ps_ltr",  #
    "hs_nt": "heading_style_normal_text",
    "ds_pw": "page_width",
    "ds_ph": "page_height",
    "ds_mb": "marg_bottom",
    "ds_ml": "marg_left",
    "ds_mt": "marg_top",
    "ds_mr": "marg_right",
    "snapshot": "snapshot",
    "lgs_l": "language",
    "hs_h1": "head_style1",
    "hs_h2": "head_style2",
    "hs_h3": "head_style3",
    "hs_h4": "head_style4",
    "hs_h5": "head_style5",
    "hs_h6": "head_style6",
    "hs_st": "head_style_st",
    "hs_t": "head_style_t",
    "sdef_ps": "set_def_ps",
    "sdef_ts": "set_def_ts",
    "ts_bd": "bold",
    "ts_bd_i": "bold_i",
    "ts_bgc": "background_color",
    "ts_bgc_i": "background_color_i",
    "ts_ff": "font_family",
    "ts_ff_i": "font_family_i",
    "ts_fgc": "foreground_color",
    "ts_fgc_i": "foreground_color_i",
    "ts_fs": "font_size",
    "ts_fs_i": "font_size_i",
    "ts_it": "italic",
    "ts_it_i": "italic_i",
    "ts_sc": "small_caps",
    "ts_sc_i": "small_caps_i",
    "ts_st": "strikethrough",
    "ts_st_i": "strikethrough_i",
    "ts_un": "underline",
    "ts_un_i": "underline_i",
    "ts_va": "vert_align",
    "ts_va_i": "vert_align_i",
    "ps_al": "alignment",
    "ps_al_i": "alignment_i",
    "ps_awao": "ps_awao",  #
    "ps_awao_i": "ps_awao_i",  #
    "ps_hd": "heading_style",
    "ps_hdid": "heading_id",
    "ps_ifl": "indent_first_line",
    "ps_ifl_i": "indent_first_line_i",
    "ps_il": "indent_line",
    "ps_il_i": "indent_line_i",
    "ps_ir": "ps_ir",  #
    "ps_ir_i": "ps_ir_i",  #
    "ps_klt": "ps_klt",  #
    "ps_klt_i": "ps_klt_i",  #
    "ps_kwn": "ps_kwn",  #
    "ps_kwn_i": "ps_kwn_i",  #
    "ps_ls": "line_space",
    "ps_ls_i": "line_space_i",
    "ps_sa": "space_af_pgraph",
    "ps_sa_i": "space_af_pgraph_i",
    "ps_sb": "space_bf_pgraph",
    "ps_sb_i": "space_bf_pgraph_i",
    "ps_sm": "ps_style",
    "ps_sm_i": "ps_style_i",  #
    "ps_ts": "ps_ts",  #
    "cv": "cv",  #
    "opValue": "opValue",
    "op": "op",
    "opIndex": "opIndex",
    "ds_hi": "ds_hi",  #
    "sugid": "sug_id",
    "id": "id",
    "null": "null",
    "msfd": "sug_del",  # mark string for delete
    "usfd": "undo_sug_del",  # undo string for delete
    "sas": "sug_adj_style",
    "rvrt": "revert",
    "de": "del_elem",
    "ae": "add_elem",
    "ue": "update_elem",
    "te": "tether_elem",
    "mlti": "mlti",
    "i_ht": "img_ht",
    "i_wth": "img_wth",
    "i_src": "img_src",
    "i_cid": "img_cosmoId",

    # mostly related to insertion of kix objects in page
    "ls_nest": "ls_nest",  #
    "spi": "spi",  #
    "epm": "epm",  #
    "et": "et",  #
    "ls_ts": "ls_ts",  #
    "ls_id": "ls_id",  #
    "ee_eo": "ee_eo",  #
    "le_nb": "le_nb",  #
    "hfe_hft": "hfe_hft",  #
}

''' other properties

eo_type  element something type
b_a
eo_mb  element something margin bottom
eo_ad  ?
eo_mt  margin top
eo_mr  margin right
eo_ml  margin left
-- involves lists
le_nb contains
    nl_0 - nl_8, each one of nl_1...8 contains properties describing formats of indention level
b_gf  %0...%8 for nl_0 ... nl_8
b_ifl (indent first line)
b_gs  associated with bullet list
b_gt
b_ts associated with numbered lists
b_il  amount to indent each level

list insertion associated with epm: le_nb
--- '''


def remap(old_key):
    """ Remaps given key if present in mapping dictionary, or returns old_key otherwise """
    return _MAPPINGS.get(old_key, old_key)
