from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Авторизоваться', callback_data='sign_in')],
    [InlineKeyboardButton(text='Информация', callback_data='info')]])


menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Загрузить таблицу', callback_data='load_table'),
     InlineKeyboardButton(text='Информация', callback_data='info')]])


choice_action = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавление переноса строк', callback_data='add_br'),
     InlineKeyboardButton(text='Подсчет работ', callback_data='cnt')]])
