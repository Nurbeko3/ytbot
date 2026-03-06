import os
import telebot
import threading

from modules import checker, myqueues 

from dotenv import load_dotenv 
load_dotenv()

TOKEN = os.getenv("BOT_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Increase timeouts for large file uploads
telebot.apihelper.CONNECT_TIMEOUT = 90
telebot.apihelper.READ_TIMEOUT = 900 # 15 minutes for large files

                      
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, "Assalomu alaykum! Men <b>Youtube Downloader botiman!👋</b>\n\nBoshlash uchun /help buyrug'ini yuboring.")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(
        message,
        """
        <b>Shunchaki video havolasini yuboring va sifatini tanlang.</b> 😉
  <i>
  Dasturchi: @dev00111
        """, disable_web_page_preview=True,)
        
    

@bot.message_handler(func=lambda m: True)
def link_check(message):
    checker.linkCheck(bot=bot, message=message)
    # print(checker.videoURL)

# Callback handler for # getVidInfo() 
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    data = call.data.split("#")
    receivedData = data[0]
    short_id = data[1]
    
    # Retrieve URL from cache
    videoURL = checker.url_cache.get(short_id)
    
    if not videoURL:
        bot.answer_callback_query(call.id, "Xatolik: Havola muddati tugagan. Iltimos, havolani qaytadan yuboring.", show_alert=True)
        return

    bot.answer_callback_query(call.id, f"{receivedData} sifati tanlandi.")
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    myqueues.download_queue.put((call.message, videoURL, receivedData))
    queue_position = myqueues.download_queue.qsize()

    if queue_position == 1:
        bot.send_message(call.message.chat.id, "Yuklash navbatga qo'shildi.")
    else:
        bot.send_message(call.message.chat.id, f"Yuklash navbatga qo'shildi. Navbatingiz: #{queue_position}.")




    # downloader.download(bot=bot, message=call.message, userInput=receivedData, videoURL=checker.videoURL)
    # bot.send_message(call.message.chat.id, f"{videoURL} \n{receivedData} : Download Triggered!")
            
# message, videoURL, receivedData
    
download_thread = threading.Thread(target=myqueues.download_worker, args=(bot, myqueues.download_queue))
download_thread.daemon = True
download_thread.start()

print("TelegramYTDLBot is running..\n")
bot.infinity_polling()
