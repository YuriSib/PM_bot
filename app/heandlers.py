import os
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types.input_file import FSInputFile


from settings import TOKEN
from xl_worker import line_breaks, cards_count, work_cnt
import app.keyboards as kb
import sqlite_comands as sql

router = Router()
bot = Bot(TOKEN)


@router.message(F.text == '/start')
async def menu(message: Message):
    user_list = await sql.get_user()

    if user_list:
        print(f'user_list = {user_list}')
        await message.answer('Старт работы бота:', reply_markup=kb.start_menu)
    else:
        flag = False
        for user in user_list:
            if user:
                user_name, user_id = user[1], user[0]
                if str(message.from_user.id) == user_id:
                    flag = True
                    await message.answer(f'Здравствуй, {user_name}! Cтарт работы бота:', reply_markup=kb.menu)
            else:
                break
        if not flag:
            print("Флаг не тру")
            await message.answer('Старт работы бота:', reply_markup=kb.start_menu)


@router.callback_query(lambda callback_query: callback_query.data.startswith('back_to_menu'))
async def sign_in(callback: CallbackQuery, bot):
    try:
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
    except Exception:
        pass
    if callback.from_user.id != 674796107:
        await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт:', reply_markup=kb.menu)
    else:
        await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт:', reply_markup=kb.admin_menu)


class WorkerName(StatesGroup):
    name = State()


@router.callback_query(lambda callback_query: callback_query.data.startswith('sign_in'))
async def sign_in(message: Message, state: FSMContext):
    await state.set_state(WorkerName.name)
    await message.answer(f'Ваше имя')
    await bot.send_message(chat_id=message.from_user.id, text='Введите ваше имя:')


@router.callback_query(lambda callback_query: callback_query.data.startswith('work_count'))
async def sign_in(message: Message):
    current_date = datetime.now()
    formatted_date = current_date.strftime('%d-%m-%y')
    table_name = f'work_cnt_{formatted_date}.xlsx'

    verified_status = await sql.get_unverified_table()
    if verified_status:
        await work_cnt(f'/root/proj/PM_bot/{table_name}')
        await bot.send_document(chat_id=message.from_user.id, document=FSInputFile(path=f'/root/proj/PM_bot/{table_name}'))
        await sql.update_verified_status()
    else:
        await bot.send_message(chat_id=message.from_user.id, text='Новых таблиц нет!')


@router.callback_query(lambda callback_query: callback_query.data.startswith('info'))
async def get_xl(callback: CallbackQuery, bot):
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
    await bot.send_message(chat_id=callback.from_user.id,
                           text='Карточки в зависимости от их наполненности будут подразделятся на 2 типа. \n'
                                '   1. Полный - в карточке не менее 3-х строк описания, "Бренд", "Страна" и другой '
                                'аттрибут фильтрации, например "Тип". Такая карточка оценевается в 9 рублей. \n'
                                '   2. Не полный - не менее 2-х строк описания, "Бренд" и "Страна". Такая карточка '
                                'оценивается в 6 рублей.',
                           reply_markup=kb.menu)


@router.message(WorkerName.name)
async def save_user(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    name = message.text

    user_list = [name[1] for name in await sql.get_user()]
    if name not in user_list:
        with open('users.txt', 'a', encoding='utf-8') as file:
            file.write(f'{name}:{message.from_user.id}\n')

        print("Пользователь зарегестрировался!", message.chat.id, message.chat.full_name)
        await sql.add_user(message.from_user.id, name)
        await message.bot.send_message(chat_id=message.chat.id, text=f'{name}, вы успешно авторизовались!',
                                       reply_markup=kb.menu)
    else:
        await message.bot.send_message(chat_id=message.chat.id, text=f'Имя {name} уже зарегестрированно, попробуйте другое!',
                                       reply_markup=kb.menu)


class FileBox(StatesGroup):
    file = State()
    document_name = State()
    file_path = State()

    # min_cost, max_cost = State(), State()


@router.callback_query(lambda callback_query: callback_query.data.startswith('load_table'))
async def get_xl(message: Message, state: FSMContext):
    await state.set_state(FileBox.file)
    await message.answer(f'Перешлите боту таблицу для редактирования.')
    await bot.send_message(chat_id=message.from_user.id, text='Перешлите боту таблицу для редактирования.')


@router.message(FileBox.file)
async def quantity_five(message: Message, state: FSMContext):
    await state.update_data(file=message.document)

    document_name = message.document.file_name
    if not await sql.check_table(document_name):
        await state.update_data(document_name=document_name)

        file_id = message.document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        await state.update_data(file_path=file_path)

        await bot.download_file(file_path, document_name)
        if message.from_user.id != 674796107:
            await message.bot.send_message(chat_id=message.chat.id, text='Выберите что делать с таблицей',
                                           reply_markup=kb.choice_action)
        else:
            await message.bot.send_message(chat_id=message.chat.id, text='Выберите что делать с таблицей',
                                           reply_markup=kb.admin_choice_action)
    else:
        await message.bot.send_message(chat_id=message.chat.id,
                                       text='Таблица с таким именем уже есть с системе. Переименуйте ее или '
                                            'обратитесь к администратору.', reply_markup=kb.menu)


@router.callback_query(FileBox.file, lambda callback_query: callback_query.data.startswith('add_br'))
async def add_br(message: Message, state: FSMContext):
    await state.set_state(FileBox.file)
    data = await state.get_data()
    file, document_name, file_path = data['file'], data['document_name'], data['file_path']

    errors_answer = await line_breaks(document_name)
    if errors_answer:
        await message.bot.send_message(chat_id=message.from_user.id, text=errors_answer)
        await message.bot.send_message(chat_id=message.from_user.id, text='Загрузите таблицу заново', reply_markup=kb.menu)
    else:
        await message.bot.send_document(chat_id=message.from_user.id, document=FSInputFile(path=document_name))
        await message.bot.send_message(chat_id=message.from_user.id, text='Выберите пункт', reply_markup=kb.choice_action)


@router.callback_query(FileBox.file, lambda callback_query: callback_query.data.startswith('cnt'))
async def cnt_cards(message: Message, state: FSMContext):
    await state.set_state(FileBox.file)
    data = await state.get_data()
    file, document_name, file_path = data['file'], data['document_name'], data['file_path']
    user_id = message.from_user.id
    cards_amount = await cards_count(document_name)
    if type(cards_amount) is str:
        await message.bot.send_message(chat_id=user_id, text='Загрузите таблицу заново', reply_markup=kb.menu)
    elif not os.path.exists(document_name):
        await message.bot.send_message(chat_id=user_id, text='Таблица с таким именем уже существует!',
                                       reply_markup=kb.menu)
    else:
        await message.bot.send_message(chat_id=user_id,
                                       text=f'Неполные карточки: {cards_amount[0]}\nПолные карточки: {cards_amount[1]}')
        await message.bot.send_message(chat_id=user_id, text='Загрузите еще таблицу', reply_markup=kb.choice_action)


@router.callback_query(FileBox.file, lambda callback_query: callback_query.data.startswith('upload'))
async def add_table(message: Message, state: FSMContext):
    await state.set_state(FileBox.file)
    await message.answer(text='Подождите, идет обработка запроса!')
    data = await state.get_data()
    document_name = data['document_name']
    cards_amount = await cards_count(document_name)

    user_id = message.from_user.id

    await sql.add_table(document_name, cards_amount[0], cards_amount[1], user_id)
    await message.bot.send_message(chat_id=user_id,
                                   text='Карточка загружена в учетную систему!', reply_markup=kb.choice_action)


@router.callback_query(FileBox.file, lambda callback_query: callback_query.data.startswith('admin_upload'))
async def choice_user(message: Message):
    if message.from_user.id == 674796107:
        user_list = await sql.get_user()
        await message.bot.send_message(chat_id=message.from_user.id,
                                       text='Выбери пользователя', reply_markup=await kb.user_list(user_list))
    else:
        await message.bot.send_message(chat_id=message.from_user.id,
                                       text='Не достаточно прав!', reply_markup=await kb.menu)


@router.callback_query(FileBox.file, lambda callback_query: callback_query.data.startswith('имя_'))
async def add_table(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FileBox.file)
    await callback.answer(text='Подождите, идет обработка запроса!')

    data = await state.get_data()
    document_name = data['document_name']
    cards_amount = await cards_count(document_name)

    user_id = int(callback.data.replace('имя_', ''))
    await sql.add_table(document_name, cards_amount[0], cards_amount[1], user_id)
    await callback.bot.send_message(chat_id=callback.from_user.id,
                                    text='Карточка загружена в учетную систему!', reply_markup=kb.choice_action)


