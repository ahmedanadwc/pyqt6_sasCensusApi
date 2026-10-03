from pyqt6_sas_census.sas.programs import (
    build_collect_catalog_code,
    build_profile_code,
    build_query_code,
)


def test_collect_catalog_code_contains_exact_macro_parameters():
    code = build_collect_catalog_code(
        "APILIB",
        "_API_ALL_DATA",
        "https://api.census.gov/data.json",
        "&g_outputRoot",
    )

    assert code.count("%censusapi_getAllDataSets") == 1
    assert "p_outLibName=APILIB" in code
    assert "p_outDsName=_API_ALL_DATA" in code
    assert "p_dataJsonURL=%str(https://api.census.gov/data.json)" in code
    assert "p_reportOutputPath=&g_outputRoot" in code


def test_profile_code_contains_exact_macro_parameters():
    code = build_profile_code(
        "APILIB",
        "_API_ALL_DATA",
        "3",
        "&g_outputRoot",
    )

    assert code.count("%censusapi_getDsFullInfo") == 1
    assert "p_apiListingLibName=APILIB" in code
    assert "p_apiListingDsName=_API_ALL_DATA" in code
    assert "p_dsRowId=3" in code
    assert "p_reportOutputPath=&g_outputRoot" in code


def test_query_code_contains_one_chunked_macro_invocation_and_clauses():
    code = build_query_code(
        "https://api.census.gov/data/2000/dec/sf1?",
        "get=NAME",
        "for=state:*",
        "in=",
        "_114_dec_2000",
        "work.sf1_response",
        "&g_apiKey",
        50,
    )

    assert code.count("%censusapi_submitDataApiQuery") == 1
    assert "p_apiBaseURL=%STR(https://api.census.gov/data/2000/dec/sf1?)" in code
    assert "p_apiGetClause=%STR(get=NAME)" in code
    assert "p_apiForClause=%bquote(for=state:*)" in code
    assert "p_apiInClause=%bquote(in=)" in code
    assert "p_dsUniqueId=_114_dec_2000" in code
    assert "p_outDsName=work.sf1_response" in code
    assert "p_dataApiKey=&g_apiKey" in code
    assert "p_maxVarCount=50" in code
