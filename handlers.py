import re
from generate_ticket import generate_ticket


re_name = re.compile(r'^[\w\-\s]{3,40}$')
re_email = re.compile(r"\b(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)\b")


def handle_name(text, context):
    match = re.match(re_name, text)
    if match:
        context['name'] = text
        return True
    return False


def handle_email(text, context):
    matches = re.findall(re_email, text)
    if len(matches) > 0:
        context['email'] = matches[0]
        return True
    return False


def generate_ticket_handler(text, context):
    return generate_ticket(name=context['name'], email=context['email'])
