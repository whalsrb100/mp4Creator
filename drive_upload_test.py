from classes.drive import DriveUpload

if __name__ == "__main__":
    # 업로드할 파일 경로와 파일명 지정
    file_path = "TEST.TXT"
    upload_filename = "TEST.TXT"

    uploader = DriveUpload()
    uploader.upload_filename = upload_filename

    try:
        result = uploader.upload(file_path)
        print("업로드 성공:")
        print(result)
    except Exception as e:
        print("업로드 실패:", e)
