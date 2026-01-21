import importlib.util
import sys
import types
from pathlib import Path

import pytest


def make_streamlit_stub():
    """Create a minimal stub for the `streamlit` module used by the app at import time."""
    stub = types.SimpleNamespace()

    # basic functions used at top-level
    stub.set_page_config = lambda *a, **k: None
    stub.markdown = lambda *a, **k: None
    stub.write = lambda *a, **k: None
    stub.table = lambda *a, **k: None
    stub.info = lambda *a, **k: None
    stub.caption = lambda *a, **k: None
    stub.download_button = lambda *a, **k: None
    stub.error = lambda *a, **k: None
    # Provide a no-op cache_data decorator compatible with usage as @st.cache_data
    def cache_data(func=None, **kwargs):
        if func is None:
            def decorator(f):
                return f
            return decorator
        else:
            return func

    stub.cache_data = cache_data

    class _Col:
        def markdown(self, *a, **k):
            return None

    def columns(spec):
        # return as many column-like objects as requested
        n = len(spec) if hasattr(spec, "__len__") else 1
        return [_Col() for _ in range(n)]

    stub.columns = columns

    # sidebar namespace with widgets that return sensible defaults
    def _expander(*a, **k):
        class _Ctx:
            def __enter__(self_inner):
                return None

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        return _Ctx()

    sidebar = types.SimpleNamespace()
    sidebar.file_uploader = lambda *a, **k: None
    sidebar.number_input = lambda *a, **k: k.get("value", 50_000_000)
    sidebar.markdown = lambda *a, **k: None
    sidebar.header = lambda *a, **k: None
    sidebar.slider = lambda *a, **k: k.get("value", 1)
    sidebar.expander = _expander
    stub.sidebar = sidebar

    # top-level selectbox used inside the expander: return the option at index (default behaviour)
    def selectbox(label, opts, index=0, key=None):
        try:
            return opts[index]
        except Exception:
            return opts[0] if opts else None

    stub.selectbox = selectbox

    return stub


def load_module_with_stub(path: Path):
    """Load the app module while injecting a streamlit stub to avoid UI calls."""
    stub = make_streamlit_stub()
    sys.modules["streamlit"] = stub
    try:
        spec = importlib.util.spec_from_file_location("people_headcount_app_for_test", str(path))
        mod = importlib.util.module_from_spec(spec)
        # Execute the module code (it will use our stub)
        spec.loader.exec_module(mod)
        return mod
    finally:
        # Clean up the stub so it doesn't affect other tests
        sys.modules.pop("streamlit", None)


def test_compensation_display_is_positive():
    """
    Ensure the app displays compensation as positive strings (no '-' sign).
    The app currently negates compensation when formatting; this test ensures displayed
    compensation contains no minus sign.
    """
    app_path = Path(__file__).resolve().parents[1] / "people_headcount_app.py"
    mod = load_module_with_stub(app_path)

    # If the module did not create a display_df (e.g., no selected employees), skip the test.
    if not hasattr(mod, "display_df"):
        pytest.skip("display_df not present in app module (no selected employees).")

    disp = mod.display_df
    assert "Compensation (USD)" in disp.columns

    # Convert values to strings and ensure no value contains a minus sign.
    comp_values = disp["Compensation (USD)"].astype(str).tolist()
    assert all("-" not in v for v in comp_values), f"Found negative compensation display values: {comp_values}"

