import html

def sanitize_value(val):
    """
    Safely sanitizes dynamic user input for inclusion in HTML email templates.
    """
    if val is None:
        return ""
    if not isinstance(val, str):
        val = str(val)
    # Strip dangerous script tags or null bytes if present, then HTML escape
    val = val.replace('\x00', '').strip()
    return html.escape(val, quote=True)

def sanitize_context(context):
    """
    Recursively sanitizes a dictionary of template context variables.
    """
    if not isinstance(context, dict):
        return context
    
    sanitized = {}
    for key, val in context.items():
        if isinstance(val, str):
            sanitized[key] = sanitize_value(val)
        elif isinstance(val, dict):
            sanitized[key] = sanitize_context(val)
        elif isinstance(val, list):
            sanitized[key] = [
                sanitize_context(item) if isinstance(item, dict)
                else (sanitize_value(item) if isinstance(item, str) else item)
                for item in val
            ]
        else:
            sanitized[key] = val
    return sanitized
