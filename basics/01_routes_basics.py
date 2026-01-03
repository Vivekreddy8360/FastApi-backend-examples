from fastapi import FastAPI,HTTPException


app= FastAPI()

@app.get('/')

def root_url(): 
    return {'Message': 'Welcome to FastApi'}

@app.get('/sub')

def internal_url():
    return {'Message': 'Welcome to FastAPI Internal Page'}

users={
    1:{
        "name":"Vivekreddy",
        "orders": {
            101:{"item": "Laptop", "amount":5000},
            102:{"item": "Mouse","amount":5000}
        }
     },
    2:{
        "name":"Suneethareddy",
        "orders": { 
            201:{"item": "Phone", "amount":4000},
            202:{"item": "Charger", "amount":5000}
        }
     }
}

@app.get('/user/{user_id}/order/{order_id}')

def get_users(user_id:int,order_id:int):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="product Id not found")
    return users[user_id]['orders'][order_id]