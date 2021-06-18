from flask import Flask
import boto3
import socket
import sys
import json
import pymysql
import traceback

app = Flask(__name__)

print(str(sys.argv))

rdsHost=""
rdsUser=""
rdsPassword=""
rdsPort=""
rdsDBName=""

tableInitDone = False

def db_credentials():
  try:
    secret_name = sys.argv[1]
    region_name = sys.argv[2]

    # Create a Secrets Manager client
    
    client = boto3.client(service_name='secretsmanager',region_name=region_name)
    print (client)
    secretResponse = client.get_secret_value(SecretId=secret_name)
    dbSecret = json.loads(secretResponse["SecretString"])
    global rdsHost, rdsUser, rdsPassword, rdsPort, rdsDBName
    rdsHost=dbSecret["host"]
    rdsUser=dbSecret["username"]
    rdsPassword=dbSecret["password"]
    rdsPort=dbSecret["port"]
    rdsDBName=dbSecret["dbname"]
  except Exception as e:
    traceback.print_exc()




def load_db_data():
  ret = ""
  try:
    connection = pymysql.connect(host=rdsHost,
                                user=rdsUser,
                                password=rdsPassword,
                                port=rdsPort,
                                database=rdsDBName)
    with connection:
      with connection.cursor() as cursor:

          sql = "show tables"
          if cursor.execute(sql) == 0:
            ret = "<br>Creating table and loading data into RDS ...<br>"
            sql = """CREATE TABLE `tasks` (
                    `task_id` int(11) NOT NULL AUTO_INCREMENT,
                    `title` varchar(255) NOT NULL,
                    `start_date` date DEFAULT NULL,
                    `due_date` date DEFAULT NULL,
                    `status` tinyint(4) NOT NULL,
                    `priority` tinyint(4) NOT NULL,
                    `description` text,
                    `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`task_id`)
                  ) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1"""
                  
            ret += "create: " + str(cursor.execute(sql))
            sql = "INSERT INTO tasks(title,start_date,due_date,status,priority,description) VALUES ('make 3ta row 1','2020-05-14','2020-06-14',1,100,'example'),('make 3ta row 2','2020-05-14','2020-07-14',1,127,'example'),('make 3ta row 3','2020-05-14','2020-08-14',1,127,'example'),('make 3ta row 4','2020-05-14','2020-09-14',1,127,'example'),('make 3ta row 5','2020-05-14','2020-10-14',1,127,'example')"
            ret += " / insert: " + str(cursor.execute(sql)) +"<br>"
            connection.commit()
          
          
  except Exception as e:
    ret=traceback.format_exc()+"<br>"

  return ret+"</p><br>"

@app.route("/")
def hello():
  return "<html><body><p>App Tier is OK<br>"+get_my_IP()+"<br></p></body></html>"


@app.route("/db")
def query_db():

  ret = "<html><body><p>Quering RDS ...<br>"

  global tableInitDone
              
  try:

    if tableInitDone == False:
      tableInitDone = True
      ret += load_db_data()
      


    connection = pymysql.connect(host=rdsHost,
                                user=rdsUser,
                                password=rdsPassword,
                                port=rdsPort,
                                database=rdsDBName)
    with connection:
      with connection.cursor() as cursor:
          sql = "select * from tasks"
          cursor.execute(sql)
          result = cursor.fetchall()
          for row in result:
            ret += str(row)+"<br>"
        
         

  except Exception as e:
    ret+=traceback.format_exc()+"<br>"
  
  return ret+get_my_IP()+"<br></p></body></html>"


def get_my_IP():
  hostname = socket.gethostname()
  ret = f"{hostname}/"
  local_ip = socket.gethostbyname(hostname)
  ret += f"{local_ip}"
  return ret


db_credentials()


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80,debug=True, use_debugger=False, use_reloader=True)

        