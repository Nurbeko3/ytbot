import os
import yt_dlp
import requests
from telebot.types import InputMediaPhoto

# Download the YouTube Video
def download(bot, message, userInput, videoURL):
    mediaPath = os.path.join(os.getcwd(), "vids")
    if not os.path.exists(mediaPath):
        os.makedirs(mediaPath)

    downloadMsg = bot.send_message(chat_id=message.chat.id, text="<b>Tayyorlanmoqda...📥</b>")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(videoURL, download=False)
            
            # 1. Handle Carousel/Gallery
            if userInput == "To'liq Galereya":
                bot.edit_message_text(chat_id=downloadMsg.chat.id, message_id=downloadMsg.message_id, text="<b>Galereya yuborilmoqda...🖼</b>")
                media_group = []
                entries = info.get('entries', [])
                
                if not entries:
                     entries = [info]
                
                for entry in entries[:10]: # Telegram limit is 10 items
                    photo_url = entry.get('url')
                    
                    if not photo_url or "instagram.com" in photo_url:
                         thumbnails = entry.get('thumbnails')
                         if thumbnails:
                              photo_url = thumbnails[-1]['url']

                    if photo_url:
                        media_group.append(InputMediaPhoto(photo_url))
                
                if media_group:
                    bot.send_media_group(message.chat.id, media_group)
                    bot.send_message(message.chat.id, f"✅ Tayyor! <b>{info.get('title', 'Galereya')}</b>\n\n<i>Yaratuvchi: @Makkalik_yigit</i>", parse_mode="HTML")
                else:
                    bot.send_message(message.chat.id, "❌ Xatolik: Ushbu postdan rasm topilmadi.")
                
            # 2. Handle Single Photo
            elif userInput == "Rasmni yuklash":
                bot.edit_message_text(chat_id=downloadMsg.chat.id, message_id=downloadMsg.message_id, text="<b>Rasm yuborilmoqda...🖼</b>")
                photo_url = info.get('url')
                
                if not photo_url or "instagram.com" in photo_url:
                     thumbnails = info.get('thumbnails')
                     if thumbnails:
                          photo_url = thumbnails[-1]['url']
                
                if photo_url:
                    bot.send_photo(
                        message.chat.id, 
                        photo_url, 
                        caption=f"✅ <b>{info.get('title', 'Rasm')}</b>\n\n<i>Yaratuvchi: @Makkalik_yigit</i>", 
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(message.chat.id, "❌ Xatolik: Rasm havolasini topib bo'lmadi.")

            # 3. Handle Video
            else:
                import re
                height_match = re.search(r'\d+', userInput)
                height = height_match.group() if height_match else "720"

                # Check for ffmpeg
                from yt_dlp.utils import check_executable
                has_ffmpeg = check_executable('ffmpeg')
                
                if has_ffmpeg:
                    format_spec = f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
                else:
                    print("FFMPEG not found. Falling back to single file format.")
                    format_spec = f"best[height<={height}][ext=mp4]/best[ext=mp4]/best"
                
                ydl_opts.update({
                    'format': format_spec,
                    'outtmpl': os.path.join(mediaPath, '%(id)s_%(height)s.%(ext)s'),
                    'merge_output_format': 'mp4',
                })

                # Re-download with specific format
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_down:
                    down_info = ydl_down.extract_info(videoURL, download=True)
                    vid_id = down_info.get('id', 'video')
                    
                    final_filename = ""
                    for f in os.listdir(mediaPath):
                        if f.startswith(vid_id):
                            final_filename = f
                            break
                    
                    if not final_filename:
                         raise Exception("Yuklashda xatolik yuz berdi, fayl topilmadi.")

                    bot.edit_message_text(chat_id=downloadMsg.chat.id, message_id=downloadMsg.message_id, text="<b>Video yuklanmoqda...📤</b>")

                    file_path = os.path.join(mediaPath, final_filename)
                    file_size = os.path.getsize(file_path) / (1024 * 1024) # Size in MB

                    if file_size > 2000:
                        bot.send_message(message.chat.id, f"⚠️ <b>Diqqat:</b> Fayl hajmi {file_size:.1f}MB. Telegram'ning maksimal limiti 2GB (2000MB).")
                    elif file_size > 50:
                        bot.send_message(message.chat.id, f"ℹ️ <b>Ma'lumot:</b> Fayl hajmi {file_size:.1f}MB. Local API server orqali yuklanmoqda...")

                    with open(file_path, 'rb') as video:
                        bot.send_video(
                            message.chat.id, 
                            video, 
                            thumb=requests.get(down_info.get('thumbnail'), timeout=10).content if down_info.get('thumbnail') else None,
                            caption=f"<b>Nomi:</b><i> {down_info.get('title')} </i>\n<b>Havola:</b><i> {videoURL} </i>\n<b>Sifati:</b><i> {userInput} </i>\n\n<i><b>Yaratuvchi: @Makkalik_yigit</b></i>",
                            parse_mode="HTML",
                            timeout=600 # 10 minutes timeout for this specific upload
                        )
                    
                    if os.path.exists(file_path):
                        os.remove(file_path)

    except Exception as e:
        error_msg = str(e)
        if "Request Entity Too Large" in error_msg or "413" in error_msg:
             error_msg = "Fayl juda katta (50MB dan ortiq). Telegram bot API orqali bunday katta fayllarni yuborib bo'lmaydi."
        
        bot.send_message(message.chat.id, f"❌ <b>Xatolik yuz berdi:</b>\n{error_msg}", parse_mode="HTML")
        print(f"Download Error: {e}")

    finally:
        try:
            bot.delete_message(downloadMsg.chat.id, downloadMsg.message_id)
        except:
            pass
