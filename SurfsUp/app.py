from flask import Flask, jsonify

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt


#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()

Base.prepare(autoload_with=engine)

station = Base.classes.station
measurement = Base.classes.measurement

#################################################
# Global Variables 
#################################################

# Initialize variables used by multiple endpoints
session = Session(engine)

# Queries most recent date, and calculates the date one year before
recentDate = session.query(measurement).order_by(measurement.date.desc()).first()
yearAgoDate = dt.datetime.strptime(recentDate.date, "%Y-%m-%d") - dt.timedelta(days=366)

session.close()

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def homepage():
    return (
        f"Ash's Climate App<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/2010-01-01<br/>"
        f"/api/v1.0/2010-01-01/2017-08-23"
    )



@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    # Query date and prcp tuples for last 366 days
    last12Data = session.query(measurement.date, measurement.prcp).filter(
    measurement.date > yearAgoDate).all()

    session.close()

    # Create dict of query results, append to list, and return JSON 
    last12JSONList = []
    for date, prcp in last12Data:
        last12Dict = {}
        last12Dict[date] = prcp
        last12JSONList.append(last12Dict)

    return jsonify(last12JSONList)



@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)

    # Query station name and ID
    stationsQuery = session.query(station.name, station.station).all()

    session.close()

    # Create a dict of query results, append to list, and return JSON
    stationsJSONList = []
    for name, id in stationsQuery:
        stationDict = {}
        stationDict["name"] = name
        stationDict["id"] = id
        stationsJSONList.append(stationDict)

    return jsonify(stationsJSONList)



@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    # Count rows of data by station, and return the most active
    activeStation = session.query(measurement.station).group_by(
    measurement.station).order_by(func.count(measurement.station).desc()).first()

    # Query date and tobs tuples for last 366 days
    last12tobs = session.query(measurement.date, measurement.tobs).filter(
    measurement.date > yearAgoDate, measurement.station == activeStation.station).all()

    session.close()

    # Create a dict of query results, append to list, and return JSON
    tobsJSONList = []
    for date, tobs in last12tobs:
        tobsDict = {}
        tobsDict[date] = tobs
        tobsJSONList.append(tobsDict)

    return jsonify(tobsJSONList)



@app.route("/api/v1.0/<startDate>")
def start(startDate):
    session = Session(engine)

    # Check if entered date appears in database
    startValid = session.query(measurement.date).filter(
        measurement.date == startDate).all()
    

    # If date does not appear in database, throw error
    if startValid == []:
        session.close()
        return jsonify({"error": "Invalid date."}), 404


    # Query min, max, and avg of tobs for specified date range
    startStats = session.query(func.min(measurement.tobs), 
        func.max(measurement.tobs), func.avg(measurement.tobs)).filter(
        measurement.date >= startDate).first()
    
    session.close()
    
    # Create dict of query results and return JSON
    startJSON = {"min": startStats[0], "max": startStats[1], "avg": startStats[2]}

    return jsonify(startJSON)




@app.route("/api/v1.0/<startDate>/<endDate>")
def end(startDate, endDate):
    session = Session(engine)

    # Check if entered dates appears in database
    startValid = session.query(measurement.date).filter(
        measurement.date == startDate).all()
    endValid = session.query(measurement.date).filter(
        measurement.date == endDate).all()
    
    # If dates does not appear in database, throw error
    if endValid == [] or startValid == []:
        session.close()
        return jsonify({"error": "Invalid date."}), 404


    # Query min, max, and avg of tobs for specified date range
    endStats = session.query(func.min(measurement.tobs), 
        func.max(measurement.tobs), func.avg(measurement.tobs)).filter(
        measurement.date >= startDate, measurement.date <= endDate).first()
    
    # If query returns null value, throw error
    if None in endStats:
        session.close()
        return jsonify({"error": "Invalid range."}), 404
    
    session.close()
    
    # Create dict of query results and return JSON
    endJSON = {"min": endStats[0], "max": endStats[1], "avg": endStats[2]}

    return jsonify(endJSON)


if __name__ == '__main__':
    app.run(debug=True)
