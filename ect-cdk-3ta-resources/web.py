from flask import Flask
import sys
import traceback
import urllib.request
import socket

app = Flask(__name__)

print(str(sys.argv))

appDNS = sys.argv[1]

@app.route("/")
def hello():
  return "<html><body><p>Web Tier is OK<br>"+get_my_IP()+"</p></body></html>"


@app.route("/app")
def call_app_layer():

  ret = ""

  try:

    webURL = urllib.request.urlopen(url=appDNS)

    ret = webURL.read()
    

  except Exception as e:
    ret = "<html><body><p>"
    ret+=traceback.format_exc()+"<br>"
    ret+="</p></body></html>"

  
  return ret

@app.route("/db")
def call_db_layer():

  ret = ""

  try:

    webURL = urllib.request.urlopen(url=appDNS+"/db")

    ret = webURL.read()
    

  except Exception as e:
    ret = "<html><body><p>"
    ret+=traceback.format_exc()+"<br>"
    ret+="</p></body></html>"

  
  return ret



def get_my_IP():
  hostname = socket.gethostname()
  ret = f"{hostname}/"
  local_ip = socket.gethostbyname(hostname)
  ret += f"{local_ip}"
  return ret

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80,debug=True, use_debugger=False, use_reloader=True)

        