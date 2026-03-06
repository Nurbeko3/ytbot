import os
import yt_dlp
import requests
from telebot.types import InputMediaPhoto

# Download the YouTube Video
def download(bot, message, userInput, videoURL):
    mediaPath = os.path.join(os.getcwd(), "vids")
    if not os.path.exists(mediaPath):
        os.makedirs(mediaPath)

    downloadMsg = bot.send_message(chat_id=message.chat.id, text="<b>Processing...📥</b>")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(videoURL, download=False)
            
            # 1. Handle Carousel/Gallery
            if userInput == "Full Gallery / Carousel":
                bot.edit_message_text(chat_id=downloadMsg.chat.id, message_id=downloadMsg.message_id, text="<b>Sending Gallery...🖼</b>")
                media_group = []
                entries = info.get('entries', [])
                
                # If flat extraction or missing entries, entries might be empty or different
                if not entries:
                     entries = [info]
                
                for entry in entries[:10]: # Telegram limit is 10 items
                    # Try to get the direct image URL from various potential fields
                    photo_url = entry.get('url')
                    
                    # If it's a flat entry or missing direct URL, use thumbnails
                    if not photo_url or "instagram.com" in photo_url:
                         thumbnails = entry.get('thumbnails')
                         if thumbnails:
                              photo_url = thumbnails[-1]['url']

                    if photo_url:
                        media_group.append(InputMediaPhoto(photo_url))
                
                if media_group:
                    bot.send_media_group(message.chat.id, media_group)
                    bot.send_message(message.chat.id, f"✅ Done! <b>{info.get('title', 'Gallery')}</b>\n\n<i>Created by @Makkalik_yigit</i>", parse_mode="HTML")
                else:
                    bot.send_message(message.chat.id, "❌ Error: Could not find images in this post.")
                
            # 2. Handle Single Photo
            elif userInput == "Download Photo":
                bot.edit_message_text(chat_id=downloadMsg.chat.id, message_id=downloadMsg.message_id, text="<b>Sending Photo...🖼</b>")
                photo_url = info.get('url')
                
                if not photo_url or "instagram.com" in photo_url:
                     thumbnails = info.get('thumbnails')
                     if thumbnails:
                          photo_url = thumbnails[-1]['url']
                
                if photo_url:
                    bot.send_photo(
                        message.chat.id, 
                        photo_url, 
                        caption=f"✅ <b>{info.get('title', 'Photo')}</b>\n\n<i>Created by @Makkalik_yigit</i>", 
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(message.chat.id, "❌ Error: Could not find image URL.")

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
                         raise Exception("Download failed, file not found.")

                    bot.edit_message_text(chat_id=downloadMsg.chat.id, message_id=downloadMsg.message_id, text="<b>Uploading Video...📤</b>")

                    file_path = os.path.join(mediaPath, final_filename)
                    with open(file_path, 'rb') as video:
                        bot.send_video(
                            message.chat.id, 
                            video, 
                            thumb=requests.get(down_info.get('thumbnail')).content if down_info.get('thumbnail') else None,
                            caption=f"<b>Title:</b><i> {down_info.get('title')} </i>\n<b>URL:</b><i> {videoURL} </i>\n<b>Quality:</b><i> {userInput} </i>\n\n<i><b>Created by @Makkalik_yigit</b></i>",
                            parse_mode="HTML"
                        )
                    
                    if os.path.exists(file_path):
                        os.remove(file_path)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")
        print(f"Download Error: {e}")

    finally:
        try:
            bot.delete_message(downloadMsg.chat.id, downloadMsg.message_id)
        except:
            pass
