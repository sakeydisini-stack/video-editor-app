import os, subprocess, uuid, wave
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from google import genai
from google.genai import types

ROOT=Path(__file__).parent.resolve(); UPLOADS=ROOT/"uploads"; OUTPUTS=ROOT/"outputs"
UPLOADS.mkdir(exist_ok=True); OUTPUTS.mkdir(exist_ok=True)
app=Flask(__name__,static_folder="static"); app.config["MAX_CONTENT_LENGTH"]=500*1024*1024
ALLOWED={".mp4",".mov",".mkv",".webm",".m4v"}
def run(cmd):
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode: raise RuntimeError(p.stderr[-2000:] or "FFmpeg failed")
@app.get("/")
def index(): return send_from_directory(ROOT/"static","index.html")
@app.post("/api/dub")
def dub_video():
 key=request.form.get("api_key","").strip()
 if not key: return jsonify(error="សូមបញ្ចូល Gemini API Key ជាមុនសិន។"),400
 f=request.files.get("video"); voice=request.form.get("voice","female").lower()
 if not f or not f.filename: return jsonify(error="សូមជ្រើសរើសវីដេអូ។"),400
 ext=Path(secure_filename(f.filename)).suffix.lower()
 if ext not in ALLOWED: return jsonify(error="ទម្រង់ដែលគាំទ្រ៖ MP4, MOV, MKV, WEBM, M4V។"),400
 job=uuid.uuid4().hex; src=UPLOADS/f"{job}{ext}"; audio=UPLOADS/f"{job}.wav"; speechfile=OUTPUTS/f"{job}_speech.wav"; out=OUTPUTS/f"{job}_khmer.mp4"
 f.save(src)
 try:
  run(["ffmpeg","-y","-i",str(src),"-vn","-ac","1","-ar","16000",str(audio)])
  client=genai.Client(api_key=key); uploaded=client.files.upload(file=str(audio))
  try:
   tr=client.models.generate_content(model="gemini-2.5-flash",contents=[uploaded,"Listen to the spoken audio and translate it into natural conversational Khmer (ភាសាខ្មែរ). Return only the Khmer translation, no explanation. Preserve names and meaning."])
   khmer=(tr.text or "").strip()
  finally:
   try: client.files.delete(name=uploaded.name)
   except Exception: pass
  if not khmer: raise RuntimeError("Gemini មិនបានផ្តល់អត្ថបទបកប្រែទេ។")
  prompt="Read this text clearly and naturally in Cambodian Khmer. "+("Use a masculine-sounding voice. " if voice=="male" else "Use a feminine-sounding voice. ")+"Do not add or translate words. Text: "+khmer
  tts=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon" if voice=="male" else "Kore")))))
  data=None
  for part in (tts.candidates[0].content.parts if tts.candidates else []):
   if getattr(part,"inline_data",None) and part.inline_data.data: data=part.inline_data.data; break
  if not data: raise RuntimeError("Gemini TTS មិនបានបង្កើតសំឡេងទេ ឬម៉ូដែលនេះមិនមានសិទ្ធិប្រើក្នុងគណនីរបស់អ្នក។")
  with wave.open(str(speechfile),"wb") as wf:
   wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000); wf.writeframes(data)
  run(["ffmpeg","-y","-i",str(src),"-i",str(speechfile),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(out)])
  return jsonify(ok=True,download_url=f"/download/{out.name}",translated_text=khmer)
 except Exception as e: return jsonify(error=str(e)),500
 finally:
  for p in (src,audio,speechfile):
   try: p.unlink(missing_ok=True)
   except Exception: pass
@app.get("/download/<path:filename>")
def download(filename):
 if not filename.endswith("_khmer.mp4"): return jsonify(error="Not found"),404
 return send_from_directory(OUTPUTS,filename,as_attachment=True)
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT","8080")),debug=False)
