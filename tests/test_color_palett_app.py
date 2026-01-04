import sys
import pytest

import color_palett_app as app


def test_find_closest_simple():
    # Two reds and one green: red closer
    target = '#ff0000'
    candidates = ['#ff0001', '#00ff00', '#fe0000']
    assert app.find_closest(target, candidates) == '#fe0000'


def test_parse_args_all(monkeypatch):
    test_argv = [
        'prog', '#abcdef',
        '-s', 'square_scheme',
        '--ods-file', 'mydata.ods',
        '-v', '-v',
    ]
    monkeypatch.setattr(sys, 'argv', test_argv)
    args = app.parse_args()
    assert args.base_color == '#abcdef'
    assert args.strategy == 'square_scheme'
    assert args.ods_file == 'mydata.ods'
    assert args.verbose == 2


@pytest.mark.slow
def test_main_integration_tetradic(capsys, monkeypatch):
    # Use the default data/golden.ods for available inks
    monkeypatch.setenv('PYTHONWARNINGS', 'ignore')
    monkeypatch.setattr(sys, 'argv', [
        'prog', '#ff0000',
        '-s', 'tetradic',
        # use default ods-file
    ])
    app.main()
    out = capsys.readouterr().out.strip().splitlines()
    # Expect one header and 4 palette lines
    assert out[0] == 'Generated palette:'
    assert len(out) == 5
    # First entry should be the base color
    assert out[1].startswith('  #ff0000')
