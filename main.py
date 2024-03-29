#!/usr/bin/env python3
#
from fastapi import FastAPI, HTTPException, Depends
from typing import Optional
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import razorpay
from dotenv import load_dotenv
import os

load_dotenv()


USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")
RZP_API_KEY_ID = os.getenv("RZP_API_KEY_ID")
RZP_API_KEY_SECRET = os.getenv("RZP_API_KEY_SECRET")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Allows these methods
    allow_headers=["*"],  # Allows all headers
)

security = HTTPBasic()



def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

rz_client = razorpay.Client(auth=(RZP_API_KEY_ID, RZP_API_KEY_SECRET))

@app.post("/payment/")
async def payment_create(
    amount: int,
    currency: str,
    description: str,
    name: str,
    email: str,
    contact: str,
    invoice_number: str,
    payment_trench: str,
    sms_notification: Optional[bool] = False,
    email_notification: Optional[bool] = False,
    reminder_enable: Optional[bool] = False,
    authenticated: bool = Depends(authenticate),
):
    payload = {
        "amount": amount,
        "currency": currency,
        "accept_partial": False,
        "description": description,
        "notes": {
            "invoice_numer": invoice_number,
            "payment_trench": payment_trench
            },
        "customer": {
            "name": name,
            "email": email,
            "contact": contact,
        },
        "notify": {
            "sms": sms_notification,
            "email": email_notification
        },
        "reminder_enable": reminder_enable,
    }

    try:
        payment_link = rz_client.payment_link.create(payload)
        return payment_link
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payment/")
async def payment_get(authenticated: bool = Depends(authenticate)):
    try:
        payment_links = rz_client.payment_link.all()
        return payment_links
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payment/{payment_id}")
async def payment_get(payment_id: str):
    try:
        payment_link = rz_client.payment_link.fetch(payment_id)
        return payment_link
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/payment/")
async def payment_delete( payment_link_id : str, authenticated: bool = Depends(authenticate)):
    try:
        rz_client.payment_link.cancel(payment_link_id)
        return {"message": "Payment link canceled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
