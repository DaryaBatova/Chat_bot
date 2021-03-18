import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import logging
import handlers
from models import UserState, Registration
from pony.orm import db_session

try:
    import settings
except ImportError:
    exit('DO cp settings.py.default settings.py and set token!')

log = logging.getLogger('bot')


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s',
            datefmt='%d-%m-%y %H:%M'
        )
    )
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler('bot.txt', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s',
        datefmt='%d-%m-%Y %H:%M'
    ))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)

    log.setLevel(logging.DEBUG)


class Bot:
    """
    Сценарий регистрации на конференцию через vk.com.
    Use python3.9

    Поддерживает ответы на вопросы про дату, место проведения и сценарий регистрации:
    - спрашиваем имя
    - спрашиваем email
    - сообщаем об успешной регистрации
    Если шаг не пройден, задаем уточняющий вопрос до тех пор, пока шаг не будет пройден.
    """
    def __init__(self, group_id, token):
        """ Конструктор класса.

        :param group_id: group id из группы vk
        :param token: секретный токен
        """
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        """ Запуск echo бота. """
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception as err:
                log.exception('Error in the processing of the event')

    @db_session
    def on_event(self, event):
        """ Отправляет сообщение-ответ на запрос пользователя.

        :param event: VkBotMessageEvent object
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info('Пришло сообщение типа %s', event.type)
            return

        # определяем id пользователя и текст сообщения
        user_id = event.object.peer_id
        text = event.object.text
        state = UserState.get(user_id=str(user_id))

        # находится ли пользователь в некотором сценарии
        if state is not None:
            # продолжаем сценарий
            text_to_send = self.continue_scenario(text, state)
        else:
            # определяем потребность пользователя
            for intent in settings.INTENTS:
                log.debug(f'User gets {intent}')

                if any(token in text.lower() for token in intent['tokens']):
                    if intent['answer']:
                        text_to_send = intent['answer']
                    else:
                        text_to_send = self.start_scenario(user_id, intent['scenario'])
                    break
            else:
                text_to_send = settings.DEFAULT_ANSWER

        self.api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id
        )

    def start_scenario(self, user_id, scenario_name):
        """Начать сценарий для пользователя.

        :param user_id: id пользователя
        :param scenario_name: имя соответствуюшего сценария
        :return: сообщение, которое необходимо отправить пользователю.
        """
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        text_to_send = step['text']
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})
        return text_to_send

    def continue_scenario(self, text, state):
        """Продолжить сценарий для пользователя.

        :param user_id: id пользователя
        :param text: сообщение пользователя
        :param state:
        :return: сообщение, которое необходимо отправить пользователю.
        """
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            text_to_send = next_step['text'].format(**state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                log.info('Зарестрирован: {name} {email}'.format(**state.context))
                Registration(name=state.context['name'], email=state.context['email'])
                state.delete()
        else:
            # повторить шаг текущего сценария
            text_to_send = step['failure_text'].format(**state.context)

        return text_to_send


if __name__ == '__main__':
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
