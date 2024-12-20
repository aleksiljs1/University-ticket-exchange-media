# from website import create_app


# app = create_app()

# if __name__ == '__main__':
#     app.run(debug=True) #run flask server every time we change sth on the server
# #only run this web server if we run this file directly


# main.py
from website import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
