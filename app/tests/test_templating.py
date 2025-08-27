import pytest
from app.domain.templating import render_template

def test_template_strict():
    subject_tpl = "Hello {{name}}"
    html_tpl = "Hi {{name}}"
    lead_dict = {"name": "Test"}
    subject, html = render_template(subject_tpl, html_tpl, lead_dict)
    assert subject == "Hello Test"
    assert html == "Hi Test"
    # Missing variable should raise
    with pytest.raises(Exception):
        render_template(subject_tpl, html_tpl, {})
