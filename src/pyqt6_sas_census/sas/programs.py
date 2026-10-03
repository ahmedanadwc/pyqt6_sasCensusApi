"""Pure builders for Census API SAS macro programs."""


def build_collect_catalog_code(
    out_lib: str,
    out_ds: str,
    data_json_url: str,
    report_path: str,
) -> str:
    """Build the SAS program that collects the Census dataset catalog."""
    return f"""/* Collect all Census Data API datasets metadata */
%censusapi_getAllDataSets(
    p_outLibName={out_lib}
  , p_outDsName={out_ds}
  , p_dataJsonURL=%str({data_json_url})
  , p_reportOutputPath={report_path}
);
"""


def build_profile_code(
    api_listing_lib: str,
    api_listing_ds: str,
    row_id: str,
    report_path: str,
) -> str:
    """Build the SAS program that profiles one catalog dataset row."""
    return f"""/* Compose complete profile of the specified dataset */
%censusapi_getDsFullInfo(
    p_apiListingLibName={api_listing_lib}
  , p_apiListingDsName={api_listing_ds}
  , p_dsRowId={row_id}
  , p_reportOutputPath={report_path}
);
"""


def build_query_code(
    api_base_url: str,
    get_clause: str,
    for_clause: str,
    in_clause: str,
    dataset_id: str,
    out_dataset: str,
    api_key_ref: str,
    max_var_count: int,
) -> str:
    """Build the SAS program that submits a chunked Census API query."""
    return f"""/* Submit Census Data API query with variable chunking */
%censusapi_submitDataApiQuery(
    p_apiBaseURL=%STR({api_base_url})
  , p_apiGetClause=%STR({get_clause})
  , p_apiForClause=%bquote({for_clause})
  , p_apiInClause=%bquote({in_clause})
  , p_dsUniqueId={dataset_id}
  , p_outDsName={out_dataset}
  , p_dataApiKey={api_key_ref}
  , p_maxVarCount={max_var_count}
);
"""
