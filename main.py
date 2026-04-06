import os
import shutil
import zipfile
import glob
from typing import List
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiofiles

app = FastAPI(title="778 TXT Processor") # ini bisa diganti 

# Mount static files (optional)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed/FNL"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def process_txt_files(input_dir: str):
    """Process all 778*.txt files and create numbered FNL files"""
    files = sorted(glob.glob(os.path.join(input_dir, "778*.txt")))
    if not files:
        return 0, []

    counter = 1
    processed_files = []

    for file_path in files:
        base_name = os.path.basename(file_path)
        x1 = base_name.split('_')[0]

        output_filename = f"{counter:03d}_{x1}_FNL.txt"
        output_path = os.path.join(PROCESSED_DIR, output_filename)

        with open(file_path, 'r', encoding='utf-8') as f, \
             open(output_path, 'w', encoding='utf-8') as out:
            found = False
            for line in f:
                stripped = line.strip()
                if stripped and x1 in stripped:
                    out.write(stripped + '\n')
                    found = True

        if found:
            processed_files.append(output_filename)
        counter += 1

    return len(files), processed_files


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...)):
    uploaded_count = 0
    is_zip = False

    # Clear previous uploads and processed files
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(PROCESSED_DIR, ignore_errors=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    for file in files:
        if file.filename.endswith('.zip'):
            is_zip = True
            zip_path = os.path.join(UPLOAD_DIR, file.filename)
            async with aiofiles.open(zip_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)

            # Extract zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(UPLOAD_DIR)
            uploaded_count += 1
            break  # Process only one ZIP

        elif file.filename.endswith('.txt'):
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            uploaded_count += 1

    if uploaded_count == 0:
        raise HTTPException(status_code=400, detail="No valid .txt or .zip files uploaded")

    # Process the files
    total_input, processed_list = process_txt_files(UPLOAD_DIR)

    return {
        "message": "Processing completed successfully!",
        "uploaded_files": uploaded_count,
        "processed_input_files": total_input,
        "generated_fnl_files": len(processed_list),
        "files": processed_list
    }


@app.get("/download/")
async def download_results():
    if not os.listdir(PROCESSED_DIR):
        raise HTTPException(status_code=404, detail="No processed files found")

    zip_path = "FNL_Results.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(PROCESSED_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, PROCESSED_DIR))

    return FileResponse(zip_path, media_type="application/zip", filename="FNL_Results.zip")
