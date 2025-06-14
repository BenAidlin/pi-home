from httpx import AsyncClient
from fastapi.openapi.docs import get_swagger_ui_html
import psutil
import cv2
from decouple import config
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.middleware.auth_middleware import AuthMiddleware
from app.utils.token_utils import create_access_token


GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = config("GOOGLE_REDIRECT_URI")
REDIRECT_URI = config("REDIRECT_URI")


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token",
)


app = FastAPI()
app.add_middleware(AuthMiddleware)
camera = cv2.VideoCapture(0)

@app.get("/")
async def home():
    return RedirectResponse("/auth/google")

@app.get("/auth/google", include_in_schema=False)
async def google_auth():
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20email%20profile"
    )
@app.get("/auth/google/callback", include_in_schema=False)
async def google_auth_callback(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    async with AsyncClient() as client:
        token_response = await client.post(
            token_url,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Could not retrieve token: {token_response.text}",
            )

        token_data = token_response.json()

        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )

        if user_info_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Could not retrieve user info: {user_info_response.text}",
            )

        user_info = user_info_response.json()

    # Create a JWT token
    access_token = create_access_token(data=user_info)
    response = RedirectResponse(url=str(REDIRECT_URI))

    response.set_cookie(
        key="Authorization",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,  # Set to True in production for HTTPS
        samesite="lax",
    )

    # Redirect to frontend with the token
    return response


@app.get("/system-info")
async def get_system_info():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_percent = psutil.cpu_percent(interval=1)

    return {
        "cpu_usage_percent": f"{cpu_percent}%",
        "memory_usage": {
            "total": f"{memory.total / 1_073_741_824:.2f} GB",
            "used": f"{memory.used / 1_073_741_824:.2f} GB",
            "available": f"{memory.available / 1_073_741_824:.2f} GB",
            "usage_percent": f"{memory.percent}%",
        },
        "disk_usage": {
            "total": f"{disk.total / 1_073_741_824:.2f} GB",
            "used": f"{disk.used / 1_073_741_824:.2f} GB",
            "free": f"{disk.free / 1_073_741_824:.2f} GB",
            "usage_percent": f"{disk.percent}%",
        },
    }


@app.get("/app", include_in_schema=False)
async def custom_swagger_ui_html():
    # Get default Swagger UI HTML as a string
    swagger_html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="Custom Swagger UI"
    ).body.decode("utf-8")  # decode bytes to string

    iframe_html = """
        <div style="margin-top: 20px; text-align:center;">
            <h2>Live Camera Stream</h2>
            <iframe
                width="640"
                height="480"
                src="/video-stream"
                frameborder="0"
                allowfullscreen>
            </iframe>
        </div>
    """

    # Inject the iframe right before </body> tag
    modified_html = swagger_html.replace("</body>", iframe_html + "</body>")

    # Return the modified HTML as response
    return HTMLResponse(content=modified_html, status_code=200)

@app.get("/video-stream")
async def video_stream():
    def generate_frames():
        while True:
            success, frame = camera.read()  # Capture a frame from the camera
            if not success:
                break

            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)

            # Yield the frame in the HTTP response
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

    # Return the stream response
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
