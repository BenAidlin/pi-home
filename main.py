from httpx import AsyncClient
from fastapi.openapi.docs import get_swagger_ui_html
from decouple import config
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.middleware.auth_middleware import AuthMiddleware
from app.routers.sys_info_router import sys_info_router
from app.routers.video_streaming import video_router
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
app.include_router(sys_info_router)
app.include_router(video_router, prefix="/video-stream")
app.add_middleware(AuthMiddleware)
camera = None


@app.get("/", include_in_schema=False)
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
