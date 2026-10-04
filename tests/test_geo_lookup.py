from pyqt6_sas_census import geo_lookup


def test_geo_json_ships_inside_the_package():
    path = geo_lookup.find_geo_json()
    assert path.parent == geo_lookup._PKG_DIR


def test_load_geo_rows_returns_full_paths():
    rows = geo_lookup.load_geo_rows()
    assert len(rows) == 51
    assert {"region", "division", "state", "state_fips", "state_abbrev"} <= set(rows[0])
