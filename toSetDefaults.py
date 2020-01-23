from extraLogic import shouldBePreFormatted
import psycopg2
try:
    connection = psycopg2.connect(user = "acpntihfuaixij",
                                  password = "0d4d9e9d7d7c4f424ddd2c3056b12ff2f187e2d6d1316fa6717e82cc8e9d473b",
                                  host = "ec2-174-129-227-146.compute-1.amazonaws.com",
                                  port = "5432",
                                  database = "dc40r85arbm903")

    cursor = connection.cursor()
    # Print PostgreSQL Connection properties
    print ( connection.get_dsn_parameters(),"\n")

    # Print PostgreSQL version
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("You are connected to - ", record,"\n")
    print("--------------------------------------------")
    cursor.execute("SELECT * FROM review;")
    for row in cursor:
        review = row[2]
        isPreFormatted = shouldBePreFormatted(review)
        cursor2 = connection.cursor()
        cursor2.execute(f"UPDATE review SET ispreformatted = {isPreFormatted} WHERE isbn = '{row[1]}';")
    connection.commit()


except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)
finally:
    #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")