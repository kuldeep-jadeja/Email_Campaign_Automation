from jinja2 import Environment, StrictUndefined, UndefinedError
from typing import Tuple, Dict

class SilentUndefined(StrictUndefined):
    """Custom undefined that returns empty string for missing variables"""
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ''

def render_template(subject_tpl: str, html_tpl: str, lead_dict: Dict) -> Tuple[str, str]:
    # Add default values for common missing fields
    template_data = {
        # Lead fields
        'first_name': '',
        'last_name': '',
        'name': '',
        'email': '',
        'company': '',
        'provider': '',
        'status': '',
        
        # Account/sender fields
        'account_signature': '',
        'sender_name': '',
        'sender_email': '',
        'sender_first_name': '',
        'sender_last_name': '',
        
        # Business fields
        'business_name': '',
        'website': '',
        'phone': '',
        'address': '',
        
        # Campaign fields
        'campaign_name': '',
        'unsubscribe_link': '#',
        
        **lead_dict  # Override with actual lead data
    }
    
    # Create name fallbacks if missing
    if not template_data.get('name') and (template_data.get('first_name') or template_data.get('last_name')):
        template_data['name'] = f"{template_data.get('first_name', '')} {template_data.get('last_name', '')}".strip()
    
    if not template_data.get('first_name') and template_data.get('name'):
        parts = template_data['name'].split(' ', 1)
        template_data['first_name'] = parts[0] if parts else ''
        template_data['last_name'] = parts[1] if len(parts) > 1 else ''
    
    # Use provider as company fallback if company is missing
    if not template_data.get('company') and template_data.get('provider'):
        template_data['company'] = template_data['provider']
    
    # Convert empty strings to more user-friendly defaults for display
    display_defaults = {
        'first_name': template_data.get('first_name') or 'there',
        'name': template_data.get('name') or 'there',
        'company': template_data.get('company') or 'your company'
    }
    template_data.update(display_defaults)
    
    env = Environment(undefined=SilentUndefined)
    subject = env.from_string(subject_tpl).render(**template_data)
    html = env.from_string(html_tpl).render(**template_data)
    return subject, html

def append_signature(html: str, sig_html: str) -> str:
    if sig_html:
        return html + "<br>" + sig_html
    return html
