import os
from dotenv import load_dotenv
import telebot
import tempfile
from datetime import date
from xlsxwriter.workbook import Workbook
from collections import defaultdict
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from database import *
from controller import *
 
load_dotenv()
API_KEY = os.getenv("API_KEY")
bot = telebot.TeleBot(API_KEY)

db = DatabaseManager("expenses.db")
db.create_databases()
users_dict = defaultdict(list)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hello! Type / to see available actions")

# processing functions for /add
@bot.message_handler(commands=['add'])
def query_title(message):
    expense_item = ExpenseItem()
    userid = message.from_user.id
    users_dict[userid] = expense_item
    users_dict[userid].userid = userid
    title_msg = bot.send_message(message.from_user.id, "Let's get you started. Type in expense name and send message.", reply_markup=gen_markup(-1))
    bot.register_next_step_handler(title_msg, process_title)

def process_title(title_msg):
    users_dict[title_msg.from_user.id].title = title_msg.text
    query_amount(title_msg)

def query_amount(message):
    amount_msg = bot.send_message(message.from_user.id, "How much did it cost? Type in a number.", reply_markup=gen_markup(0))
    bot.register_next_step_handler(amount_msg, process_amount)

def process_amount(amount_msg):
    amount = amount_msg.text
    if amount.isdigit() or amount.replace(".", "").isdigit():
        users_dict[amount_msg.from_user.id].amount = float(amount)
        query_paymentmode(amount_msg)
    else:
        bot.reply_to(amount_msg, "Invalid amount. Try again in whole numbers or decimals please.")
        query_amount(amount_msg)

def query_paymentmode(message):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Paylah/ Paynow', 'Debit', 'Credit', 'Cash', 'Exit', 'Back')
    paymentmode_msg = bot.send_message(message.from_user.id, "How did you pay? Select an option",  reply_markup=markup)       
    bot.register_next_step_handler(paymentmode_msg, process_paymentmode)

def process_paymentmode(paymentmode_msg):
    if paymentmode_msg.text == 'Exit':
        bot.clear_step_handler_by_chat_id(paymentmode_msg.from_user.id)
        bot.send_message(paymentmode_msg.from_user.id, "Restarted. Type in a command to begin.")
    elif paymentmode_msg.text == 'Back':
        query_amount(paymentmode_msg)
    elif paymentmode_msg.text not in ['Paylah/ Paynow', 'Debit', 'Credit', 'Cash']:
        bot.reply_to(paymentmode_msg, "Select a method from the keyboard provided. Try again")
        query_paymentmode(paymentmode_msg)
    else:
        users_dict[paymentmode_msg.from_user.id].paymentmode = paymentmode_msg.text
        query_date(paymentmode_msg)

def query_date(message):
    date_msg = bot.send_message(message.from_user.id, 
    "Date of expense? If today, just enter '.' Else, format is DD MM YYYY", reply_markup=gen_markup(2))
    bot.register_next_step_handler(date_msg, process_date)

def process_date(date_msg):
    try:
        dates = None
        if date_msg.text == ".":
            ts = int(date_msg.date)
            dates = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
        else:
            dates_lst = date_msg.text.split(" ")
            dates_lst = [int(i) for i in dates_lst]
            dates = date(dates_lst[2],dates_lst[1], day = dates_lst[0])
        users_dict[date_msg.from_user.id].date = dates
        query_remark(date_msg)
    except:
        bot.send_message(date_msg.from_user.id, "Incorrect date format. Try again!")
        query_date(date_msg)

def query_remark(message):
    remarks_msg = bot.send_message(message.from_user.id, "Extra Remarks? Enter '.' if none", reply_markup=gen_markup(3))
    bot.register_next_step_handler(remarks_msg, process_remarks)

def process_remarks(remarks_msg):
    if remarks_msg.text != ".":
        users_dict[remarks_msg.from_user.id].remarks = remarks_msg.text
    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        db.insert_expense(conn, cur, users_dict[remarks_msg.from_user.id].tuple_form())
        bot.send_message(remarks_msg.chat.id, "Succesfully added! Press /add to add more")

queries = [query_title, query_amount, query_paymentmode, query_date, query_remark]

# exit and back implementation
def gen_markup(previous_step):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
    InlineKeyboardButton("Exit", callback_data="exit"),
    InlineKeyboardButton("Back", callback_data=f"back {previous_step}")
    )
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action = call.data.split()
    if action[0] == "exit":
        bot.clear_step_handler_by_chat_id(call.from_user.id)
        bot.send_message(call.from_user.id, "Restarted. Type in a command to begin.")
    elif action[0] == "back":
        previous_step = int(action[1])
        bot.clear_step_handler_by_chat_id(call.from_user.id)
        if previous_step == -1:
            bot.send_message(call.from_user.id, "Restarted. Type in a command to begin.")            
        else:
            queries[previous_step](call)


@bot.message_handler(commands=['retrieve'])
def retrieve(message):
    with sqlite3.connect("expenses.db") as conn:
        userid = message.from_user.id
        cur = conn.cursor()
        data = db.retrieve_user_data(cur, userid)
        if len(data) == 0:
            bot.send_message(message.chat.id, "There are no entries in your expenses")
        else:
            msg = ""
            for i, row in enumerate(data):
                msg += f"{i+1}. {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]} \n"
            bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=['download_excel'])
def download_excel(message):
    # fname = "./xlsx_folder/expenses_" + str(message.from_user.first_name) + ".xlsx"
    fname = "expenses_" + str(message.from_user.first_name) + ".xlsx"
    with sqlite3.connect("expenses.db") as conn:
        userid = message.from_user.id
        cur = conn.cursor()
        data = db.retrieve_user_data(cur, userid)
        if len(data) == 0:
            bot.send_message(message.chat.id, "Sorry, there are no entries in your expenses")
        else:
            with tempfile.TemporaryFile(suffix='.xlsx', mode='w+b') as temp:
                workbook = Workbook(temp)
                worksheet = workbook.add_worksheet()
                # print(temp)
                # print(temp.read())
                bot.send_message(message.chat.id, "Generating excel...")
                for i, row in enumerate(data):
                    for j, value in enumerate(row):
                        if j <= 1: # remove the numbering and userid from data
                            continue
                        elif j > 1: # fill in the gap left from userid removal
                            j -= 2
                        worksheet.write(i+1, j, value)
                header = ["Title", "Amount", "Mode of Payment", "Date", "Remarks"]
                header_format = workbook.add_format({'bold': True, 'bottom': 2})
                for colnum, data in enumerate(header):
                    worksheet.write(0, colnum, data, header_format)
                workbook.close()
                temp.seek(0)
                bot.send_document(message.chat.id, document=temp, visible_file_name=fname)
        # bot.send_document(message.chat.id, document=open(str(fname), "rb"), visible_file_name=fname)

@bot.message_handler(commands=['delete_last_expense'])
def delete_last_expense(message):
    with sqlite3.connect("expenses.db") as conn:
        cur = conn.cursor()
        if db.has_entries(cur):
            db.delete_last_expense(conn, cur)
            bot.send_message(message.chat.id, "Last entry deleted!")
        else:
            bot.send_message(message.chat.id, "No more entries to delete")

# @bot.message_handler(commands=['delete_expense'])
# def delete_expense(message):
#     expenseid = message.text.split()[-1]
#     expenseid = int(expenseid)
#     print(expenseid)
#     with sqlite3.connect("expenses.db") as conn:
#         cur = conn.cursor()
#         if db.has_entries(cur):
#             try:
#                 expense = db.retrieve_expense(conn, cur, expenseid)
#                 print("expense", expense)
#                 bot.send_message(message.from_user.id, f"Delete {expense}?")
#                 markup = ReplyKeyboardMarkup(one_time_keyboard=True)
#                 markup.add('Yes', 'No')
#                 confirm = bot.send_message(message.from_user.id, f"Delete {expense}?",  reply_markup=markup)
#                 bot.register_next_step_handler(confirm, confirm_deletion, expenseid)
#             except:
#                 bot.send_message(message.chat.id, "Sorry, no such entry to delete")

# def confirm_deletion(message, expenseid):
#     if message.text == "no":
#         bot.clear_step_handler_by_chat_id(message.from_user.id)
#     elif message.text == "yes":
#         with sqlite3.connect("expenses.db") as conn:
#             cur = conn.cursor()
#             db.delete_expense(conn, cur, expenseid)

bot.infinity_polling()
