from scrape.config import load_config

def test_load_config_tmp(tmp_path):
    y = tmp_path / "cfg.yaml"
    y.write_text("output_dir: 'data'\nrate_limit:\n  max_requests_per_minute: 5\n")
    s = load_config(str(y))
    assert s.output_dir == "data"
    assert s.rl_max_rpm == 5
