#!/usr/bin/env python3
"""Cache only the exact guest-approved food photographs as local WebP files."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps
from urllib.parse import quote, unquote, urlencode, urlparse
from urllib.request import Request, urlopen
import base64, hashlib, json, re, time

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images"
OUT.mkdir(exist_ok=True)
manifest = json.loads((ROOT / "photo-sources.json").read_text("utf-8"))

def fetch(url, referer="", timeout=19):
    headers = {
      "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36",
      "Accept":"image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
      "Accept-Language":"en-US,en;q=0.8"
    }
    if referer: headers["Referer"] = referer
    with urlopen(Request(url,headers=headers), timeout=timeout) as res:
        data=res.read(14_000_001)
        ctype=res.headers.get("Content-Type","")
    if len(data)>14_000_000 or data[:1]==b"<" or "text/html" in ctype:
        raise ValueError("not a supported image, or too large")
    return data

def convert(data, path):
    im=Image.open(BytesIO(data))
    im=ImageOps.exif_transpose(im).convert("RGB")
    if min(im.size)<100: raise ValueError("image too small")
    im.thumbnail((1000,900),Image.Resampling.LANCZOS)
    im.save(path,"WEBP",quality=81,method=4)
    if path.stat().st_size<1500: raise ValueError("empty converted image")

def options(entry):
    url=entry["url"]; opts=[url]
    if "commons.wikimedia.org/wiki/Special:FilePath/" in url:
        filename=unquote(urlparse(url).path.split("Special:FilePath/")[-1]).replace("_"," ")
        api="https://commons.wikimedia.org/w/api.php?"+urlencode({"action":"query","format":"json","titles":"File:"+filename,"prop":"imageinfo","iiprop":"url","iiurlwidth":"900"})
        try:
            with urlopen(Request(api,headers={"User-Agent":"HomeMenuPhotoCache/1.0 (personal recipe website)"}),timeout=10) as res:
                d=json.load(res)
            for p in d.get("query",{}).get("pages",{}).values():
                info=p.get("imageinfo",[])
                if info:
                    found=info[0].get("thumburl") or info[0].get("url")
                    if found: opts.insert(0,found)
        except Exception: pass
        fname=filename.replace(" ","_")
        md5=hashlib.md5(fname.encode("utf-8")).hexdigest()
        raw="https://upload.wikimedia.org/wikipedia/commons/"+md5[0]+"/"+md5[:2]+"/"+quote(fname)
        opts.append(raw)
    else:
        opts.append("https://images.weserv.nl/?url="+quote(url,safe="")+"&w=900")
    return list(dict.fromkeys(opts))

def job(e):
    fn=OUT/e["filename"]
    if fn.exists() and fn.stat().st_size>1500:
        return {"id":e["id"],"ok":True,"status":"existing"}
    errors=[]
    for url in options(e):
        try:
            convert(fetch(url,e.get("source","")),fn)
            return {"id":e["id"],"ok":True,"status":"saved","size":fn.stat().st_size}
        except Exception as exc:
            errors.append(type(exc).__name__+": "+str(exc)[:140])
    return {"id":e["id"],"ok":False,"status":"download failed","errors":errors}

# The two user-uploaded images are already embedded in the previous index.html.
# Save them as actual local files and replace their base64 references.
index=ROOT/"index.html"
html=index.read_text("utf-8")
m=re.search(r"const photos=(\{.*?\});\nconst selected=",html,re.S)
if not m: raise RuntimeError("Site photo map missing")
photos=json.loads(m.group(1))
for id in (9,12):
    p=photos.get(str(id))
    if p and p["img"].startswith("data:image/jpeg;base64,"):
        convert(base64.b64decode(p["img"].split(",",1)[1]),OUT/("%02d.webp"%id))
        p["img"]="images/%02d.webp"%id
        print("Saved user-provided photo",id,flush=True)
if any(photos[str(i)]["img"].startswith("data:") for i in (9,12)):
    raise RuntimeError("Failed to extract user photos")
reduced=html[:m.start(1)]+json.dumps(photos,ensure_ascii=False,separators=(",",":"))+html[m.end(1):]
index.write_text(reduced,"utf-8")

results=[]
with ThreadPoolExecutor(max_workers=7) as executor:
    futures=[executor.submit(job,e) for e in manifest]
    for f in as_completed(futures):
        row=f.result();results.append(row)
        print(str(row["id"]).zfill(2), "OK" if row["ok"] else "FAILED",flush=True)
results.sort(key=lambda x:x["id"])
good=sum(x["ok"] for x in results)
(OUT/"download-report.json").write_text(json.dumps({"requested":len(manifest),"success":good,"failed":len(manifest)-good,"details":results},ensure_ascii=False,indent=2),"utf-8")
print("External images saved:",good,"/",len(manifest),flush=True)
# Downloads may fail for unavailable origins, while the menu remains functional.
