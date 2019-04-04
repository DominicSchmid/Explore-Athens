import mysql.connector
import datetime as dt

cnx = mysql.connector.connect(
    user="root", password="mysql#5BT", host="localhost", database="python", auth_plugin="mysql_native_password")


mysql_f = "%Y-%m-%d %H:%M:%S"

cursor = cnx.cursor()
vals = ("%" + "stschdom" + "%",)
cursor.execute(
    "SELECT * FROM users JOIN positions ON users.u_id = positions.p_id WHERE kuerzel LIKE %s", vals)

res = cursor.fetchall()
cnx.close()  # Close due to resource leakage
if res is None:
    print("None")

entry = res[len(res) - 1]  # Get last position
print(entry)

d = {
    "kuerzel": entry[1],
    "vorname": entry[2],
    "nachname": entry[3],
    "x": entry[6],
    "y": entry[7],
    "dt": dt.datetime.strptime(str(entry[8]), mysql_f).strftime("%x %X")
}
print(d)
cnx.close()


def write_to_db(db, song):
    cursor = db.cursor()
    # datetime.datetime.strptime(song["date"], "%c").strftime("%Y-%m-%d %H:%M:%S")
    newdate = None

    cnx = db_connect()
    cursor = cnx.cursor()

    """try:
        sql = INSERT INTO spotify(artist, song, date, duration, explicit)
        VALUES (%s, %s, %s, %s, %s)
        vals = (song["artist"], song["song"], newdate,
                song["duration_ms"], song["explicit"])
        cursor.execute(sql, vals)
        db.commit()
        cursor.close()
        # time.sleep(0.5)
    except Exception as e:
        print(e)
        print("Failed inserting song")"""
