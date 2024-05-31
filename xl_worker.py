from openpyxl import load_workbook
import gspread
import asyncio
from datetime import datetime


async def line_breaks(dir_path_):
    wb = load_workbook(dir_path_)
    ws = wb.active

    col_num = 1
    for row in ws.iter_rows(min_row=1, max_row=1, max_col=10):
        for cell in row:
            col_num += 1
            value = cell.value
            if not value or 'писание' in value:
                break
        if col_num == 9:
            return 'Не найдена колонка "Описание"'

    max_row = ws.max_row

    for row in range(2, max_row+1):
        old_value = ws.cell(row=row, column=col_num-1).value
        if not old_value:
            continue
        new_value = old_value.replace('•', ' <br> •').replace('<br>  <br> •', ' <br> •')
        letter_idx = 0
        for letter in new_value:
            if letter == ' ' or letter == '<' or letter == 'b' or letter == 'r' or letter == '>':
                letter_idx += 1
            else:
                break
        new_value = new_value[letter_idx:]
        ws.cell(row=row, column=col_num-1).value = new_value

    wb.save(dir_path_)


async def cards_count(dir_path_):
    wb = load_workbook(dir_path_)
    ws = wb.active

    column_name, column_desc, column_pic = False, False, False
    col_num = 1
    for row in ws.iter_rows(min_row=1, max_row=1, max_col=10):
        for cell in row:
            col_num += 1
            value = cell.value

            if not value:
                break

            if 'Наименование' in value:
                column_name = col_num
            elif 'Описание' in value:
                column_desc = col_num
            elif 'фото' in value:
                column_pic = col_num
    if not column_name or not column_desc or not column_pic:
        return 'Не найдена одна из колонок, "Описание", "Наименование", "Ссылки на фото"'

    max_row = ws.max_row
    min_cost, max_cost, zero_cost = 0, 0, 0
    for row in range(1, max_row+1):
        description = ws.cell(row=row+1, column=column_desc-1).value
        pic_cnt = ws.cell(row=row+1, column=column_pic-1).value

        if not description and not pic_cnt:
            if not ws.cell(row=row+1, column=1).value:
                break
            else:
                zero_cost += 1
                continue
        else:
            cnt_str = description.count('•')
            cnt_photo = len(pic_cnt.split(','))

            if cnt_str >= 4 and cnt_photo >= 3:
                max_cost += 1
            else:
                min_cost += 1

    return min_cost, max_cost


async def add_user(user_name):
    gc = gspread.service_account(filename='creds.json')
    sheet = gc.open("Work_count").sheet1

    for col in range(2, 15):
        if not sheet.cell(row=1, col=col).value:
            sheet.update_cell(row=1, col=col, value=user_name)
            sheet.update_cell(row=2, col=col, value='max_cost')
            sheet.update_cell(row=2, col=col+1, value='min_cost')
            sheet.update_cell(row=2, col=col+2, value='Всего')

            sheet.update_cell(row=1, col=col+3, value=user_name+' Д')
            sheet.update_cell(row=2, col=col+3, value='max_cost')
            sheet.update_cell(row=2, col=col+4, value='min_cost')
            sheet.update_cell(row=2, col=col+5, value='Всего')
            break


async def add_result(min_cost, max_cost, table_name, user):
    gc = gspread.service_account(filename='creds.json')
    sheet = gc.open("Work_count").sheet1

    remotely = True if 'Д.xlsx' in table_name else False

    user_list = sheet.row_values(1)
    user_col = user_list.index(user)+1

    current_date = datetime.now().strftime('%d.%m.%Y')
    date_list = sheet.col_values(1)

    if current_date in date_list:
        cur_row = date_list.index(current_date)
    else:
        rows = sheet.get_all_values()
        cur_row = len(rows)
        sheet.update_cell(row=cur_row+1, col=1, value=current_date)

    if not remotely:
        sheet.update_cell(row=cur_row + 1, col=user_col, value=min_cost)
        sheet.update_cell(row=cur_row + 1, col=user_col + 1, value=max_cost)
        sheet.update_cell(row=cur_row + 1, col=user_col + 2, value=max_cost + min_cost)
    else:
        sheet.update_cell(row=cur_row + 1, col=user_col + 3, value=min_cost)
        sheet.update_cell(row=cur_row + 1, col=user_col + 4, value=max_cost)
        sheet.update_cell(row=cur_row + 1, col=user_col + 5, value=max_cost + min_cost)


if __name__ == "__main__":
    # asyncio.run(add_user('Жорик'))
    asyncio.run(add_result(13, 64, 'Таблица(дата).xlsx', 'Жорик'))