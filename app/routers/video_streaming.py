from fastapi import APIRouter
import cv2
from fastapi.responses import RedirectResponse, StreamingResponse
from decouple import config

video_router = APIRouter()
REDIRECT_URI = config("REDIRECT_URI")
camera = None
@video_router.post("/enable")
async def enable_video_steam():
    global camera
    camera = cv2.VideoCapture(0)
    return RedirectResponse(str(REDIRECT_URI))


@video_router.post("/disable")
async def disable_video_steam():
    global camera
    camera = None
    return RedirectResponse(str(REDIRECT_URI))


@video_router.get("/", include_in_schema=False)
async def video_stream():
    def generate_frames():
        if not camera:
            yield "Enable video stream to view camera data"
            return
        while True:
            success, frame = camera.read()  # Capture a frame from the camera
            if not success:
                break

            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)

            # Yield the frame in the HTTP response
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame" if camera else None,
    )
