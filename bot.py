import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from telegram.ext import Application, ContextTypes
import nest_asyncio, asyncio
nest_asyncio.apply()


from database import DataBaseFetch

TOKEN = "6929830229:AAEXbYO97fey0HwecRuIPFTLXYT-WxzgigI"
MANAGER = {"id":"ali_zeighamiyan"}
ROLES = ["employee", "stockman"]
WORKERS = []

ADD_WORKER = {"text":"Add Worker", "callback_data":"add_worker"}
ADD_ANOTHER_WORKER =  {"text":"Add Another Worker", "callback_data":"add_worker"}
VIEW_WORKER = {"text":"View Workers", "callback_data":"view_workers"}
BACK = {"text":"Back", "callback_data":"back"}
ASSIGN_ROLE = {"text":"Assign Role", "callback_data":"select_role"}
DELETE_WORKER = {"text":"Delete Worker", "callback_data":"deleteworker"}

MANAGER_START_MENU = [ADD_WORKER, VIEW_WORKER]
WORKER_START_MENU = [VIEW_WORKER]
EDIT_WORKER_MENU = [ASSIGN_ROLE, DELETE_WORKER, BACK]
ADD_WORKER_NAME_MENU = [BACK]
ADD_WORKER_ID_MENU = [BACK, ADD_ANOTHER_WORKER]

class ButtonMaker:
    def __init__(self) -> None:
        self.keyboard = []
    def build_keyboard(self, text_callback_list:list[dict]):
        for text_callback_data in text_callback_list:
            self.keyboard.append([InlineKeyboardButton(text_callback_data["text"], callback_data=text_callback_data["callback_data"])])
        return self
    def get_markup(self):
        reply_markup = InlineKeyboardMarkup(self.keyboard)
        self.keyboard = []
        return reply_markup
        
        

button_maker = ButtonMaker()
buttons = {
           "MANAGER_START_MENU" :  button_maker.build_keyboard(MANAGER_START_MENU).get_markup(),
           "WORKER_START_MENU" : button_maker.build_keyboard(WORKER_START_MENU).get_markup(),
           "ADD_WORKER_NAME_MENU" : button_maker.build_keyboard(ADD_WORKER_NAME_MENU).get_markup(),
           "ADD_WORKER_ID_MENU" : button_maker.build_keyboard(ADD_WORKER_ID_MENU).get_markup(),
           "EDIT_WORKER_MENU" : button_maker.build_keyboard(EDIT_WORKER_MENU).get_markup(),
           }

db_fetcher = DataBaseFetch(db_name="user_data.db")
# In-memory storage for users, workers, and roles

managers = {"ali_zeighamiyan": True}  # Replace with actual manager usernames

# def get_worker_buttons_markup(workers:list, msg:str):
#     if not workers :
#         workers.append(("No Worker Found!", ))
#     worker_buttons = [InlineKeyboardButton(worker[0], callback_data=f"worker-{msg}:{worker[0]}") for worker in workers]
#     worker_markup = InlineKeyboardMarkup.from_column(worker_buttons)
#     return worker_markup


async def edit_worker(query, context):
    worker_name = query.data.split(":")[1]
    context.user_data["selected-worker"] = worker_name
    reply_markup = buttons["EDIT_WORKER_MENU"]
    await query.edit_message_text(f'Worker:{worker_name}', reply_markup=reply_markup)

async def start_menu(query, context) -> None:
    """Send a message when the command /start is issued."""
    context.user_data["pos-stack"] = ["start_menu"]
    username = context.user_data["username"]
    if username in managers:
        reply_markup = buttons["MANAGER_START_MENU"]
    else:
        reply_markup = buttons["WORKER_START_MENU"]
    await query.edit_message_text('Welcome to the Worker Manager Bot! Choose an option:', reply_markup=reply_markup)
    
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    context.user_data["pos-stack"] = ["start_menu"]
    username = update.message.from_user.username
    if username in managers:
        reply_markup = buttons["MANAGER_START_MENU"]
    else:
        reply_markup = buttons["WORKER_START_MENU"]
    await update.message.reply_text('Welcome to the Worker Manager Bot! Choose an option:', reply_markup=reply_markup)
    
        
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses for various commands."""
    query = update.callback_query
    await query.answer()

    data = query.data
    username = query.from_user.username
    context.user_data["username"] = username

    if data != "back":
        context.user_data["pos-stack"].append(data)
    if data == 'add_worker' and username in managers:
        await add_worker(query, context)
    elif data == 'select_role' and username in managers:
        await select_role(query, context)
    elif data == 'view_workers':
        await view_workers(query, context)
    elif data == "delete_worker":
        await delete_worker(query, context)
        
    elif data.startswith("handle_role_assignment"):
        await handle_role_assignment(query, context)
    
    elif data.startswith("edit_worker"):
        await edit_worker(query, context)
    elif data == 'back':
        context.user_data["pos-stack"].pop()
        pos_to_go = context.user_data["pos-stack"][-1]
        await globals()[pos_to_go](query, context)

async def view_workers(query, context):
    """Display the list of workers."""
    workers = db_fetcher.get_workers()
    if not workers: workers.append(("No Worker Found!", ))
    button_maker.build_keyboard([{"text":worker[0], "callback_data":f"edit_worker:{worker[0]}"}
                                    for worker in workers])
    button_maker.build_keyboard([BACK])
    worker_markup = button_maker.get_markup()
    await query.edit_message_text('Choose From Workers', reply_markup=worker_markup)

    # await query.edit_message_text(f"Workers:\n{worker_list}")

async def select_role(query, context):
    worker_name = context.user_data["selected-worker"]
    button_maker.build_keyboard([{"text":role, "callback_data":f"handle_role_assignment:{role}"} 
                                 for role in ROLES])
    role_markup = button_maker.build_keyboard([BACK]).get_markup()
    
    # role_buttons = [InlineKeyboardButton(role, callback_data=f"role-assign:{role}") for role in ROLES]
    # role_markup = InlineKeyboardMarkup.from_column(role_buttons)
    await query.edit_message_text(f'Select a role to assign to {worker_name}:', reply_markup=role_markup)

async def handle_role_assignment(query, context):
    role_name = query.data.split(":")[1]
    worker_name = context.user_data.get('selected-worker')
    if worker_name:
        db_fetcher.assign_role_to_worker(worker_name=worker_name, role_name=role_name)
        await query.edit_message_text(f'Assigned role {role_name} to worker {worker_name}.')
        

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    # user_id = update.message.from_user.id

    if context.user_data.get('adding_worker'):
        state = context.user_data.get("state")
        
        if state == "AddWorkerName":
            context.user_data["worker_detail"] = {}
            worker_name = update.message.text
            context.user_data["worker_detail"]["name"] = worker_name
            context.user_data["state"] = "AddWorkerID"
            reply_markup = buttons["ADD_WORKER_NAME_MENU"]
            await update.message.reply_text(f'Got it! Now enter the related username for : {worker_name}', reply_markup=reply_markup)

        elif state == "AddWorkerID":
            worker_name = context.user_data["worker_detail"]["name"]
            worker_username = update.message.text
            context.user_data["worker_detail"]["username"] = worker_username
            context.user_data['adding_worker'] = False
            context.user_data["state"] = None
            db_fetcher.add_worker(worker_name, worker_username)
            reply_markup = buttons["ADD_WORKER_ID_MENU"]
            await update.message.reply_text(f'Worker {worker_name} with username {worker_username} added.', 
                                           reply_markup=reply_markup)
            
    elif context.user_data.get('adding_role'):
        role_name = update.message.text
        context.user_data['adding_role'] = False
        await update.message.reply_text(f'Role {role_name} added.')

async def add_worker(query: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt the user to add a worker."""
    context.user_data['adding_worker'] = True
    context.user_data["state"] = "AddWorkerName"
    await query.edit_message_text('Please enter the name of the worker to add.')

async def delete_worker(query, context):
    worker_name = context.user_data.get("selected-worker")
    db_fetcher.delete_worker(worker_name=worker_name)
    await query.edit_message_text(f'Worker {worker_name} deleted')
    

async def main() -> None:
    """Start the bot."""
    # Replace 'YOUR_TOKEN_HERE' with your bot's token

    
    # Create a new application instance
    application = Application.builder().token(TOKEN).build()

    # Add handlers to the dispatcher
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    await application.run_polling()

if __name__ == '__main__':
    try:
        # Use asyncio.run if no event loop is running
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If there's already a running event loop, use it
        print("Event loop is already running")
        task = loop.create_task(main())
        loop.run_until_complete(task)
    else:
        # Otherwise, create a new event loop and run the main coroutine
        asyncio.run(main())