import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
import uuid

# URL cache to store long URLs for callback_data (Telegram limit is 64 bytes)
url_cache = {}

def linkCheck(bot, message):
    linkFilter = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    userLinks = re.findall(linkFilter, message.text)

    if userLinks:
        videoURL = userLinks[0]
        qualityChecker(bot=bot, message=message, videoURL=videoURL)
    else:
        bot.reply_to(message, "🧐 <b>Hech qanday havola topilmadi!</b>\nIltimos, video havolasini yuboring.")

def qualityChecker(bot, message, videoURL):
    qualityCheckerMsg = bot.reply_to(message, "Kutilmoqda... 🔎")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'ignore_no_formats_error': True,
    }

    try:
        info = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(videoURL, download=False)
            except Exception as e:
                # If extraction fails (e.g., [Instagram] no video), try flat extraction for metadata
                error_str = str(e).lower()
                if "no video in this post" in error_str or "video" in error_str:
                    ydl_opts['extract_flat'] = True
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl_flat:
                        info = ydl_flat.extract_info(videoURL, download=False)
                elif "private" in error_str:
                    raise Exception("Bu video yopiq (shaxsiy) yoki unga kirish cheklangan.")
                elif "copyright" in error_str:
                    raise Exception("Bu video mualliflik huquqi bilan himoyalangan.")
                else:
                    raise e

            if not info:
                raise Exception("Media ma'lumotlarini olib bo'lmadi. Havola to'g'riligini tekshiring.")

            # Detect type
            is_playlist = info.get('_type') == 'playlist' or 'entries' in info
            formats = info.get('formats', [])
            has_video = any(f.get('vcodec') != 'none' for f in formats)
            
            available_qualities = {}

            if is_playlist:
                # Instagram Carousel or Youtube Playlist
                q_name = "To'liq Galereya"
                entries = info.get('entries', [])
                count = len(entries) if entries else "Bir nechta"
                available_qualities[q_name] = {
                    "q": q_name,
                    "size": f"{count} ta element",
                    "format_id": "playlist"
                }
            elif not has_video:
                # No video format means it's likely a Photo or just metadata available
                q_name = "Rasmni yuklash"
                available_qualities[q_name] = {
                    "q": q_name,
                    "size": "Asl o'lcham",
                    "format_id": "photo"
                }
            else:
                # Standard Video Quality selection
                for f in formats:
                    height = f.get('height')
                    if height and f.get('vcodec') != 'none':
                        res_map = {2160: "4k", 1440: "2k", 1080: "1080p", 720: "720p", 480: "480p", 360: "360p", 240: "240p", 144: "144p"}
                        q_name = res_map.get(height)
                        if not q_name:
                            q_name = f"{height}p"
                        
                        filesize = f.get('filesize') or f.get('filesize_approx')
                        size_str = f"{filesize / (1024*1024):.1f} MB" if filesize else "Noma'lum"
                        
                        if q_name not in available_qualities or (filesize and available_qualities[q_name]['size_raw'] < filesize):
                             available_qualities[q_name] = {
                                 "q": q_name,
                                 "size": size_str,
                                 "size_raw": filesize or 0,
                                 "format_id": f.get('format_id')
                             }

            # Generate unique ID for this search
            short_id = str(uuid.uuid4())[:8]
            url_cache[short_id] = videoURL
            
            # Sort: Playlists first, then video resolutions
            sorted_qualities = list(available_qualities.values())
            if not is_playlist and has_video:
                sorted_qualities = sorted(sorted_qualities, key=lambda x: int(re.search(r'\d+', x['q']).group()) if re.search(r'\d+', x['q']) else 0, reverse=True)

        def gen_markup():
            markup = InlineKeyboardMarkup() 
            for value in sorted_qualities: 
                callbackData = f"{ value['q'] }#{ short_id }"
                button = InlineKeyboardButton(text=f"{value['q']} ({value['size']})", callback_data=callbackData)
                markup.add(button)
            return markup

        try:
            bot.delete_message(qualityCheckerMsg.chat.id, qualityCheckerMsg.message_id)
        except:
            pass
            
        bot.send_message(chat_id=message.chat.id, text=f"📥 <b>{info.get('title', 'Media')}</b>\n\nYuklash turini tanlang:", reply_markup=gen_markup(), parse_mode="HTML")

    except Exception as e:
        print(f"Checker Error: {e}")
        try:
             # Strip color codes from error message
             clean_error = re.sub(r'\u001b\[[0-9;]*m', '', str(e))
             if "Sign in to confirm you’re not a bot" in clean_error:
                 clean_error = "YouTube bot ekanligimni aniqladi. Keyinroq qayta urinib ko'ring."
             
             bot.edit_message_text(chat_id=qualityCheckerMsg.chat.id, message_id=qualityCheckerMsg.message_id, text=f"❌ <b>Xatolik yuz berdi:</b>\n{clean_error}", parse_mode="HTML")
        except:
             bot.send_message(chat_id=message.chat.id, text=f"❌ Xatolik: {str(e)}")








