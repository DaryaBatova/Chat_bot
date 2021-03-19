from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from urllib.parse import urlencode
import hashlib
import requests

PATH_TO_IMAGE = 'images/invitation.PNG'
PATH_TO_FONT = 'fonts/Roboto-Regular.ttf'
FONT_SIZE = 20

BLACK = (0, 0, 0, 255)
Y_FOR_NAME = 160
Y_FOR_EMAIL = 215

GRAVATAR_URL = 'https://www.gravatar.com/avatar/'
DEFAULT = 'robohash'
AVATAR_SIZE = 150
AVATAR_OFFSET = (100, 100)


def get_gravatar_url(email):
    email_form = email.strip().lower().encode()
    gravatar_url = GRAVATAR_URL + hashlib.md5(email_form).hexdigest() + '?'
    gravatar_url += urlencode({'d': DEFAULT, 's': str(AVATAR_SIZE)})
    return gravatar_url


def put_text_on_image(draw, text, y_pos, width, font):
    w, _ = draw.textsize(text, font=font)
    x_pos = int(310 + (width - 370 - w) / 2)
    draw.text((x_pos, y_pos), text, font=font, fill=BLACK)


def generate_ticket(name, email):
    image = Image.open(PATH_TO_IMAGE).convert("RGBA")
    width = image.width
    font = ImageFont.truetype(PATH_TO_FONT, FONT_SIZE)

    draw = ImageDraw.Draw(image)
    put_text_on_image(draw=draw, text=name, y_pos=Y_FOR_NAME, width=width, font=font)
    put_text_on_image(draw=draw, text=email, y_pos=Y_FOR_EMAIL, width=width, font=font)

    gravatar_url = get_gravatar_url(email=email)
    response = requests.get(url=gravatar_url)
    file_like_with_avatar = BytesIO(response.content)
    avatar = Image.open(file_like_with_avatar)

    image.paste(avatar, AVATAR_OFFSET)

    temp_file = BytesIO()
    image.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file


if __name__ == '__main__':
    file = generate_ticket(name='Иван Иванов', email='ivanivanov@gmail.com')
    # email = "MyEmailAddress@example.com "
    # print(get_gravatar_url(email=email))

